# BiblionOCR Intelligent Compute and Headless Jetson Architecture

Session summary date: 2026-08-08

## 1. Strategic Thesis

BiblionOCR should be positioned as an adaptive computational humanities environment.

Core distinction:

- automation executes workflow steps
- machine learning learns from workflow outcomes
- AI assists reasoning about workflow choices
- scholar remains authority over interpretation

This framing prioritizes provenance, reproducibility, transparency, and graceful human intervention.

## 2. Resource Model

Current development model is heterogeneous:

- HP desktop for orchestration, development, and broader experimentation
- Jetson Nano as CUDA-capable network resource candidate

Target shift:

- from remote-controlled desktop
- to managed compute resource

## 3. Compute Architecture Direction

Compute Engine remains the foundation and should answer:

> What can this resource safely do for BiblionOCR?

Not:

> What can all hardware in the world theoretically do?

Core concerns:

1. resource discovery
2. capability knowledge
3. resource monitoring
4. workload planning
5. fallback and human bailout

Conceptual flow:

```text
Compute Engine
   |
   +-> Discovery
   +-> Capability Knowledge
   +-> Monitoring
   |
   v
Workload Planner
   |
   v
Provider Path (CUDA / CPU / Remote)
   |
   v
Fallback and Human Bailout
```

## 4. Capability Semantics

Use explicit capability states:

- KNOWN_GOOD
- KNOWN_UNSUITABLE
- UNKNOWN

Unknown must trigger conservative fallback.

Capability evaluation is workload-oriented, not vendor-oriented.

## 5. CUDA and Workload Fit

CUDA should be treated as provider capability, not universal default.

High-fit candidate areas include:

- image preprocessing
- feature extraction
- lightweight inference
- similarity and embedding workloads
- experimentally validated ML support tasks

Tesseract LSTM training remains primarily CPU-oriented and should not be assumed to be the first CUDA target.

## 6. Workflow Intelligence and Provenance

Adaptive workflow should remain auditable.

A future recommendation path should record:

- decision type
- model and version
- confidence
- evidence features
- compute provider and node
- accepted/rejected outcome

Goal:

- machine recommendations become inspectable evidence
- scholarly conclusions remain human-governed

## 7. Remote Jetson Node Pattern

Jetson should eventually be headless and service-oriented.

Target node responsibilities:

- compute-agent startup
- capability report
- registration
- heartbeat
- workload execution
- result and failure reporting

A graphical desktop is optional and not the architectural requirement.

## 8. Migration Discipline for Existing Nano

Before replacing current image:

1. inventory current OS, runtime, and hardware
2. capture JetPack/L4T lineage
3. backup current installation and config
4. confirm storage and boot topology
5. choose NVIDIA-supported image appropriate to Nano generation

Guiding constraint:

- newer Ubuntu version does not automatically mean better Nano target
- NVIDIA-supported stack compatibility is primary

## 9. Phased Implementation Sequence

1. preserve module-by-module delivery cadence
2. stabilize Compute Engine constraints and decision rules
3. prepare stable headless Nano base
4. introduce minimal resource registry semantics
5. ship first Nano compute-agent registration/heartbeat path
6. ship one measurable CUDA workload
7. add workload planner and controlled fallback/degradation
8. add first ML-assisted recommendation loop with provenance

## 10. Architectural Boundaries

- Compute Engine does not own scholarship.
- Workflow engine does not own hardware.
- Intelligence layer does not own compute.
- Providers do not own application logic.
- Remote nodes are resources, not remote desktops.
- ML recommendations are not scholarly conclusions.

## 11. Non-Goal Statement

BiblionOCR should not become:

- a general cloud orchestration platform
- a generic distributed-computing framework
- a hardware cataloging project

Required scope is narrower:

discover resources -> characterize capabilities -> choose execution path -> execute -> monitor -> fallback or bailout.

## 12. Current Decision

Continue established module-by-module implementation workflow.

Advance Compute Engine and Jetson architecture as a parallel, bounded track through roadmap-constrained change sets.

## 13. Companion Documents

- docs/development/COMPUTE_ENGINE_ROADMAP.md
- docs/development/COMPUTE_ENGINE_ARCHITECTURE.md
- docs/development/JETSON_PERSISTENT_LAUNCHERS.md
- docs/development/LOCAL_MASTER_SYNC_AFTER_PR.md
