# Jetson Nano Project and Page Workflow Feasibility

**Status:** Plausible path forward; implementation and on-device benchmarks pending
**First recorded:** 2026-08-18
**Review model:** Living feasibility study, updated when new workloads, providers, measurements, or workflow stages become available

## 1. Decision Summary

The Jetson Nano remains a plausible BiblionOCR managed compute provider, but it is not currently the preferred host for the unmodified Ghostscript PDF-to-TIFF pipeline.

A favorable integration depends on changing the unit of offload from a one-time shell command into a managed project/page job whose source and large intermediate files can remain on the Nano. The desktop should receive compact metadata, progress, provenance, and final artifacts rather than repeatedly transferring multi-gigabyte TIFF intermediates.

The near-term decision is therefore:

- keep local CPU execution as the deterministic default;
- retain the Nano as an explicit experimental remote provider;
- build provider-neutral job execution and measurement first;
- admit Nano workloads only when end-to-end evidence shows a workflow benefit;
- preserve automatic local fallback when the Nano is unavailable or slower than the accepted threshold.

## 2. Current Evidence

Verified Nano baseline:

- hostname: `nano`
- LAN address: `192.168.2.5`
- architecture: ARM64
- operating system: Ubuntu 18.04.6 LTS
- CUDA family: 10.2
- access model: headless SSH over wired Ethernet
- intended role: managed compute resource, not remote desktop

Measured local PDF baseline from the 2026-08-18 feasibility session:

| Workload | Input/Output | Local result |
| --- | --- | --- |
| Ghostscript PDF extraction | 21 pages from a 255 MB PDF | 1.29 seconds |
| Ghostscript 300 DPI LZW TIFF rasterization | 21 pages | 57.9 seconds |
| Generated TIFF volume | 21 pages | 2.15 GB, about 102.5 MB/page |
| Legacy TIFF decode/copy stage | 21 pages | 55.6 seconds, about 645 MB peak RAM |
| 100 Mb/s return-transfer floor | 2.15 GB | about 172 seconds before protocol overhead |

These measurements show why merely expanding a range job to the full document does not make the Nano favorable. Ghostscript does not use the Nano GPU, the Nano CPU is weaker than the current desktop CPU, and full-document raster output increases storage and transfer costs.

They also reveal opportunities: remove the legacy decode/copy pass, run conversion asynchronously, avoid returning large intermediates, and test workloads that can use CUDA or produce compact outputs.

## 3. Favorable Integration Model

The Nano should integrate below project and page workflows through Compute Engine:

```text
Project/Page Workflow
        |
        v
Compute Job Request
        |
        v
Compute Engine Provider Selection
   |                       |
Local CPU             Nano Provider
   |                       |
   +---- progress/status --+
        provenance/results
                |
                v
Project metadata + page workflow state
```

A provider-neutral job request should carry:

- project identity and project-root-relative artifact paths;
- source document hash and protected-source identity;
- workload type and required capabilities;
- full-document or bounded page scope;
- source document page count;
- Front Matter, Scripture, and Back Matter section metadata when assigned;
- output retention policy: remote intermediate, local final, or both;
- timeout, cancellation, retry, and fallback policy;
- software/provider versions required for reproducibility.

A result should return:

- success, failure, cancellation, or fallback state;
- provider and device identity;
- measured queue, compute, transfer, and total elapsed time;
- detected source page count;
- per-page completion and artifact manifest;
- output hashes and project-relative destinations;
- stderr/diagnostic summary;
- provenance suitable for project history.

## 4. Project Workflow Integration

Source registration or extraction must continue treating `NumberPages` as the canonical source-document page count. `TotalProjectPages` remains the derived page-column work-unit count.

When a Nano job reports validated PDF metadata, BiblionOCR should update the canonical project database through the existing project-database API. SQLite and JSON/CSV mirrors then remain synchronized, and project tracking can expose:

- `source_document_pages`;
- `source_page_sections`;
- `current_source_section`;
- provider/job state and provenance once those fields are introduced.

Project workflow milestones should distinguish:

1. source registered;
2. source metadata verified;
3. source conversion queued;
4. source conversion complete;
5. required final artifacts synchronized locally.

A remote intermediate alone must not mark a local-artifact milestone complete unless the workflow explicitly allows remote residency.

## 5. Page Workflow Integration

Page jobs are the safest first execution unit because they are bounded, retryable, and measurable. A page workflow should be able to request one page, a verified section, or the full page range without changing provider-specific code.

Recommended page behavior:

- schedule pages independently or in bounded batches;
- preserve project page numbering in every artifact manifest;
- resolve assigned Front Matter, Scripture, or Back Matter metadata for each page;
- publish progress without blocking the MyServer UI thread;
- retry only failed pages when outputs are deterministic;
- record the provider used per page;
- fall back to local CPU without changing artifact naming or workflow semantics.

Full-document jobs remain useful for source staging and sequential conversion, but they should emit page-level progress and resumable manifests so a late failure does not discard the whole run.

## 6. Candidate Workloads

### Near-Term Candidates

- PDF metadata and page-count inspection after one-time source staging;
- page thumbnail or preview generation with compact return artifacts;
- bounded image preprocessing experiments;
- lightweight classification or inference with a validated CUDA path;
- OCR experiments where trained data and source pages remain resident on the Nano;
- page/section batches whose final outputs are text, metadata, or compressed images.

### Conditional Candidates

- full-document extraction when the protected source is staged once and downstream processing consumes remote outputs;
- TIFF rasterization when only selected final pages return or a smaller archival format is accepted;
- multi-stage page pipelines that avoid materializing and transferring every intermediate.

### Poor Current Candidates

- unmodified Ghostscript rasterization followed by return of every 300 DPI TIFF;
- the legacy TIFF decode/copy pass;
- workloads whose dependencies do not support Ubuntu 18.04/aarch64;
- heavy training or large-model inference on the Nano's constrained memory;
- jobs without deterministic local fallback.

## 7. Implementation Phases

### Phase 0: Local Optimization and Instrumentation

- remove unnecessary TIFF decoding/copying;
- move conversion off the UI thread;
- capture queue, compute, output-size, transfer, and total timings;
- establish representative one-page, section, and full-document fixtures.

### Phase 1: Nano Provider Control Plane

- add authenticated health/capability discovery;
- add a narrow job submit/status/cancel/result contract;
- stage protected sources by content hash so unchanged files transfer once;
- report available storage, memory, thermal state, and software versions;
- keep execution allowlisted to known BiblionOCR workload types.

### Phase 2: First Page Workflow Trial

- select one compact-output workload;
- dispatch bounded page batches;
- update page progress and provenance through existing workflow ownership boundaries;
- verify deterministic artifact parity against local CPU execution;
- exercise disconnect, timeout, cancellation, and fallback behavior.

### Phase 3: Full-Document Trial

- keep source and intermediates remote;
- emit page-level resumable progress;
- return only required final artifacts and metadata;
- compare total elapsed workflow time, not compute time alone;
- admit the workload only if the acceptance gates pass.

## 8. Benchmark and Admission Gates

Every candidate must compare the same source, settings, and outputs on local CPU and Nano.

Measure:

$$
T_{total} = T_{queue} + T_{stage} + T_{compute} + T_{return} + T_{integration}
$$

Also record output parity, peak memory, remote storage growth, energy/thermal throttling where available, failure recovery, and UI responsiveness.

A Nano path is favorable when at least one is demonstrated without unacceptable correctness or maintenance cost:

- lower end-to-end elapsed workflow time;
- meaningful desktop responsiveness or resource relief;
- useful unattended/background throughput;
- CUDA-only capability that is unavailable locally;
- reusable remote residency that improves later workflow stages.

Initial admission rule:

- output parity must pass;
- failure must preserve or restore a valid local workflow state;
- local fallback must pass;
- total time must be measured, including transfers;
- the result must show a documented benefit, not merely successful execution.

## 9. Security and Operations

- Do not transmit SSH passwords through chat, logs, project metadata, or job payloads.
- Use key-based authentication and a restricted service identity before automation.
- Allowlist executable workload types and validate project-relative paths.
- Hash staged inputs and returned outputs.
- Enforce storage quotas and cleanup policy for remote intermediates.
- Treat the protected source PDF as project data with explicit retention rules.
- Preserve the known-good Nano image until the provider path justifies platform changes.

## 10. Living Update Process

Update this study whenever any of the following occurs:

- a new project/page workflow stage becomes a candidate for offload;
- local pipeline optimization changes the comparison baseline;
- a Nano benchmark produces new timing, output-size, thermal, or reliability evidence;
- Compute Engine gains execution, cancellation, provenance, or remote-provider contracts;
- network speed, Nano storage, OS, CUDA, or dependency support changes;
- the source-page section model gains routing or range-editing behavior;
- a different compact output format changes transfer economics;
- failures reveal a new fallback, security, or data-integrity requirement.

Each update should add a dated entry below and revise the decision summary if the evidence changes.

## 11. Update Ledger

### 2026-08-18

- Recorded local extraction, rasterization, legacy copy, output-volume, and network-floor measurements.
- Concluded that full-range expansion alone does not favor the Nano.
- Defined the favorable path as managed jobs, one-time source staging, remote intermediate residency, compact result return, page-level progress, provenance, and deterministic local fallback.
- Connected remote page-count results to canonical project metadata and the three-section scripture page model.
- Left on-device authenticated benchmarking pending; no Nano performance ratio is claimed.

## 12. Next Evidence-Producing Step

Optimize and instrument the local full-document path first. Then implement the smallest remote provider trial that returns compact artifacts, preferably PDF metadata/thumbnails or a bounded lightweight inference task. Use the same instrumentation and fixtures on both providers before deciding whether to advance full-document conversion.
