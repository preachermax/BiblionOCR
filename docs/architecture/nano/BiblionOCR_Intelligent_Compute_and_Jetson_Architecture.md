# BiblionOCR: Intelligent Compute, CUDA, and Headless Jetson Architecture
## Session Summary and Nano Migration Plan
### 8 August 2026

## 1. Strategic Direction

BiblionOCR should not merely advertise itself as "AI-powered OCR." Its stronger distinction is as an **adaptive computational humanities environment** in which machine intelligence assists scholarly workflows while preserving:

- provenance
- reproducibility
- transparency
- human authority over interpretation
- graceful failure and human intervention

The important architectural distinction is:

> **Automation executes the workflow.  
> Machine learning learns from the workflow.  
> AI helps reason about the workflow.  
> The scholar remains the authority over interpretation.**

This gives the AI/ML effort an intellectual purpose rather than making it a technology demonstration.

---

## 2. Available Development/Compute Resources

The current environment provides a useful heterogeneous computing laboratory:

### HP desktop

Dual boot:

- Ubuntu 24, AMD64
- Windows 10 Pro, 64-bit

Primary uses:

- development
- Linux experimentation
- GUI development and compatibility testing
- heavier ML experimentation where hardware permits
- orchestration and project administration

### Jetson Nano

Current characteristics:

- NVIDIA Jetson Nano
- 4 GB class GPU
- Ubuntu 18.04.6 LTS on AARCH64 (Linux 4.9.253-tegra)
- Headless over Ethernet with SSH access (`nano`, `192.168.2.5`)
- CUDA available
- networked to the development environment

The Nano should evolve from being a remotely controlled desktop into a **network computational resource**.

---

# 3. The Important Architectural Shift

The Nano should not need TeamViewer.

Instead of:

> "I have a Nano that I remote into."

BiblionOCR should understand:

> "I have a CUDA-capable computational resource on my network that BiblionOCR can discover and utilize."

The Nano therefore becomes a **managed resource**, not a remotely operated desktop.

A suitable headless node can:

1. boot
2. start its compute agent
3. announce its capabilities
4. register with BiblionOCR
5. wait for work
6. perform the assigned workload
7. return results
8. report status
9. wait for additional work

A desktop environment is unnecessary for this role.

---

# 4. Compute Engine Evolution

The existing Compute Engine architecture is the correct foundation.

It should discover and characterize resources without becoming a giant hardware encyclopedia.

The system should answer:

> **What can this resource safely do for BiblionOCR?**

rather than:

> What can every GPU ever manufactured do?

This keeps the knowledge base intentionally bounded.

## Proposed structure

```text
                 COMPUTE ENGINE
                       |
       +---------------+---------------+
       |               |               |
       v               v               v
 RESOURCE          CAPABILITY       RESOURCE
 DISCOVERY          KNOWLEDGE       MONITORING
       |               |               |
       +---------------+---------------+
                       |
                       v
                WORKLOAD PLANNER
                       |
             +---------+---------+
             |         |         |
             v         v         v
           CUDA       CPU      REMOTE
             |         |         |
             +---------+---------+
                       |
                       v
                FALLBACK ENGINE
                       |
                       v
                 HUMAN BAILOUT
```

The five principal concerns are:

1. Resource Discovery
2. Capability Knowledge
3. Resource Monitoring
4. Workload Planning
5. Fallback/Bailout

---

# 5. Resource Knowledge Base

The Compute Engine should maintain a **small operational knowledge base**.

It should not attempt exhaustive hardware compatibility coverage.

The machine itself reports facts.

The knowledge base interprets those facts.

For example:

```yaml
provider: nvidia_cuda

device:
  vendor: NVIDIA
  architecture: Maxwell
  memory_mb: 4096

runtime:
  cuda: "..."
  driver: "..."

capabilities:
  cuda: true
  tensor_operations: limited
  fp16: true
  inference: true

constraints:
  max_model_size_mb: ...
  recommended_batch_size: ...
```

The exact schema should be established later.

The key principle is that the database should describe **BiblionOCR-relevant capabilities and constraints**, not every possible characteristic of the hardware.

---

# 6. Capability States

Unknown hardware should never be treated as capable merely because it looks promising.

Use three fundamental states:

```text
KNOWN GOOD       -> use
KNOWN UNSUITABLE -> avoid
UNKNOWN          -> conservative fallback
```

This is particularly important when other developers contribute machines with unfamiliar NVIDIA GPUs, CUDA versions, drivers, TensorRT installations, or Linux distributions.

BiblionOCR should discover what it can verify and conservatively decline what it cannot.

---

# 7. Task-Oriented Capability Knowledge

Capability should be evaluated against workloads.

For example:

| Capability | Jetson Nano | Desktop GPU | CPU |
|---|---:|---:|---:|
| Image preprocessing | Yes | Yes | Yes |
| OCR preprocessing | Yes | Yes | Yes |
| ML inference | Yes | Yes | Yes |
| Large-model inference | Limited | Yes | Fallback |
| Model training | Limited | Yes | Yes |
| Embeddings | Yes | Yes | Yes |
| Workflow orchestration | Yes | Yes | Yes |

These are conceptual classifications, not final Nano benchmarks.

The actual Compute Engine should eventually discover/profile and validate the relevant capabilities.

The important idea is:

> The planner asks whether a resource can safely execute a particular BiblionOCR workload.

---

# 8. Decisive ML Process Flow

As NVIDIA GPUs become more common, Compute Engine needs to be decisive without becoming reckless.

A workload should follow a process such as:

```text
                   REQUEST WORK
                        |
                        v
                Can preferred GPU
                   execute it?
                  /            \
                YES             NO
                 |               |
                 v               v
              Use GPU        Can CPU execute?
                                /       \
                              YES        NO
                               |          |
                               v          v
                           Use CPU      Bailout
                                         |
                                         v
                                Human intervention
```

More advanced degradation can be:

```text
Preferred:
GPU model A

Fallback:
GPU model B

Fallback:
CPU model C

Final:
Manual workflow
```

This is **graceful degradation**, not failure.

A core architectural principle should be:

> **BiblionOCR shall prefer accelerated computation when a suitable resource is available, but no workflow shall depend upon optional acceleration unless explicitly designated as mandatory.**

---

# 9. Where CUDA Actually Matters

CUDA should not be forced into tasks where it offers little benefit.

Tesseract LSTM training remains primarily CPU-oriented and should not be treated as the obvious CUDA target.

More promising CUDA/ML opportunities include:

- image preprocessing
- feature extraction
- image classification
- similarity calculations
- embeddings
- lightweight inference
- anomaly detection
- learned preprocessing selection
- document/page classification
- other experimentally validated ML workloads

The Compute Engine should make CUDA available as a capability rather than assuming every workload belongs on the GPU.

---

# 10. Intelligent Workflow

The existing Workflow architecture can eventually become adaptive.

A deterministic workflow might say:

```text
Project Created
      |
Corpus Registered
      |
Images Imported
      |
Preprocessing
      |
OCR
      |
Glyph Analysis
      |
Lexical Analysis
      |
Grounding
      |
Resolution
      |
Versification
      |
Publication
```

An intelligent workflow can begin asking:

> What should happen next?

For example:

```text
OCR Result
   |
   +-- confidence = .97
   |       -> accept
   |
   +-- confidence = .61
   |       -> inspect
   |
   +-- confidence = .18
           -> reprocess
```

Eventually the system could learn that particular document/page characteristics favor particular preprocessing strategies.

Then preprocessing becomes:

> **Select the strategy most likely to produce a useful OCR result for this kind of document.**

rather than merely:

> **Run preprocessing.**

---

# 11. Learning From Scholarly Corrections

A potentially powerful future loop is:

```text
OCR
 |
v
Scholar correction
 |
v
Correction recorded
 |
v
Training/evaluation dataset
 |
v
Model evaluation
 |
v
Improved recommendation
 |
v
Future documents
```

The project therefore becomes an instrument that can learn from its own scholarly history.

This should be implemented carefully and with provenance.

The human correction must remain authoritative evidence.

---

# 12. Project Knowledge State

An adaptive project could eventually maintain a knowledge state resembling:

```text
Project
|
+-- Corpus
+-- Documents
+-- Images
+-- OCR Results
+-- Confidence Scores
+-- Corrections
+-- Models
+-- Provenance
+-- Workflow State
+-- Learned Recommendations
```

An AI system could inspect this state and make recommendations.

Example:

> Document 17 has an unusually high OCR error rate on pages 143–157. The pages share a common typographic layout. A previous preprocessing strategy improved comparable pages. Recommend reprocessing those pages with that strategy.

This is more meaningful than attaching a chatbot to BiblionOCR.

It is an **adaptive scholarly workflow**.

---

# 13. Provenance Must Extend Into ML Decisions

An automated decision should record more than the resulting setting.

Conceptually:

```yaml
decision:
  type: preprocessing_selection
  strategy: B
  reason:
    model: preprocessing_selector_v1
    confidence: 0.87
    evidence:
      - document_class: historical_print
      - page_layout: two_column
      - previous_strategy_success: 0.81

  compute:
    provider: cuda
    device: jetson_nano

  timestamp: ...

  reproducibility:
    model_version: ...
    parameters: ...
```

The scholarly artifact should eventually contain not only:

> What happened?

but:

> Why did it happen?

> Which model made the recommendation?

> What evidence was considered?

> What compute resource was used?

> What model/version/parameters were involved?

> Did the scholar accept the result?

This is where AI/ML becomes particularly compatible with the humanities.

---

# 14. Credibility and "Preeminence"

The goal should not be to establish credibility by using fashionable AI terminology.

That would weaken the project.

A stronger proposition is:

> **BiblionOCR is an adaptive computational humanities environment in which machine intelligence assists scholarly workflows while preserving provenance, reproducibility, and human authority over interpretation.**

A credible computational claim should look something like:

> The system selected preprocessing strategy C because model X predicted a 91% probability of improved OCR confidence, based on features A, B, and C. The operation was performed on CUDA device Y. OCR confidence increased from 72.4% to 89.1%. The scholar accepted the resulting transcription.

That is impressive because another researcher could potentially reproduce the experiment.

The differentiator is not merely AI.

It is **auditable computational scholarship**.

---

# 15. BiblionOCR Should Not Become a General Distributed Computing Framework

Avoid prematurely turning Compute Engine into:

- Kubernetes
- Docker orchestration
- arbitrary cluster scheduling
- distributed model training
- universal GPU abstraction
- cloud provisioning
- job federation
- a general-purpose compute platform

BiblionOCR is not trying to become AWS.

The practical requirement is much smaller:

> **Discover useful resources -> characterize them -> choose an appropriate execution path -> execute -> monitor -> recover/fallback.**

That is enough.

---

# 16. Networked Jetson Architecture

The eventual headless Nano can expose a small service layer:

```text
Jetson Nano
|
+-- Compute Agent
|
+-- Resource Reporter
|
+-- Work Receiver
|
+-- CUDA Provider
|
+-- Result Reporter
```

At boot:

```text
Jetson boots
   |
Compute Agent starts
   |
Resource discovery
   |
Capability profile generated
   |
Registration with BiblionOCR
   |
ONLINE
   |
Wait for work
```

The desktop does not need to know that the node is a Nano.

It knows something like:

```text
Node: nano-01
Architecture: ARM64
CUDA: available
GPU Memory: 4 GB
Capabilities:
    image_preprocessing
    feature_extraction
    lightweight_inference

Status:
    ONLINE
```

---

# 17. The TeamViewer Insight

Abandoning TeamViewer was therefore not merely a convenience decision.

It points toward a cleaner architecture.

Instead of using remote-desktop software to make machines feel like one desktop environment, BiblionOCR can make them **computationally discoverable resources**.

This gives us:

- less GUI overhead
- clearer separation of roles
- explicit resource discovery
- reproducible workload assignment
- resource monitoring
- better provenance
- fallback capability
- a foundation for additional compute nodes later

This is genuinely a "two birds with one stone" opportunity.

---

# 18. Headless Jetson Nano Migration

## Objective

Preserve the current known-good headless Nano baseline and only pursue image migration when there is a clear compatibility, security, or maintenance reason.

The desired result is:

```text
Jetson Nano
    |
NVIDIA-supported JetPack/L4T base
    |
Minimal/headless configuration
    |
CUDA
    |
BiblionOCR Compute Agent
    |
Network
```

## Important constraint

The exact Jetson Nano hardware generation and boot/storage configuration must be confirmed before selecting the image.

Do not erase the current SSD until the new image has been selected and the existing image/configuration has been preserved.

The Nano's supported software stack is constrained by NVIDIA's JetPack/L4T support history. A newer Ubuntu release is not necessarily appropriate simply because it is newer.

The fact that the current image is Ubuntu 18.04 does **not** mean Ubuntu 24 is a realistic target for the Nano.

For this hardware, an older NVIDIA-supported JetPack/L4T release may actually be the correct engineering choice.

---

# 19. Recommended Migration Strategy

Use:

- **Windows** for downloading/verifying the image and writing the bootable/storage media if that is the most convenient path.
- **Linux** for configuration, networking, package management, development, testing, and the BiblionOCR compute agent.

Do not make the initial migration dependent on BiblionOCR itself.

First establish a stable headless Jetson.

Then install BiblionOCR's compute service.

---

# 20. Preserve the Existing Nano First

Before replacing the SSD image:

### On the current Nano

Collect:

```bash
uname -a
cat /etc/os-release
dpkg --print-architecture
lsblk
df -h
free -h
python3 --version
nvcc --version
nvidia-smi
```

Note that `nvidia-smi` is not always the appropriate diagnostic on Jetson platforms; NVIDIA's Jetson-specific tools may be more useful depending on the installed stack.

Also capture:

```bash
dpkg -l > ~/nano-installed-packages.txt
systemctl list-unit-files --state=enabled > ~/nano-enabled-services.txt
```

Save the output somewhere off the Nano.

Also record:

- hostname
- IP/network configuration
- SSH configuration
- CUDA version
- JetPack/L4T version
- Python version
- any BiblionOCR-related software
- mount points
- SSD partition layout

---

# 21. Back Up Anything Worth Keeping

Before writing a new image, preserve:

- `/home`
- BiblionOCR-related files
- configuration files
- scripts
- SSH keys required for the new architecture
- network configuration information
- any CUDA experiments
- package lists
- service definitions

Ideally make a complete image/clone of the existing SSD before replacement.

Do not rely solely on a file copy if the existing installation contains anything difficult to reconstruct.

---

# 22. Determine the Exact JetPack/L4T Baseline

On the existing Nano, investigate:

```bash
cat /etc/nv_tegra_release
```

Also inspect:

```bash
dpkg-query -W | grep -i nvidia
```

The goal is to determine the current NVIDIA L4T/JetPack lineage.

The replacement image should be selected based on:

1. Jetson Nano model
2. boot/storage method
3. NVIDIA-supported JetPack/L4T release
4. CUDA version required
5. Python compatibility
6. BiblionOCR requirements

**Do not select an image merely because its Ubuntu version is newer.**

For Jetson hardware, the NVIDIA-supported software stack is the primary constraint.

---

# 23. Image Acquisition

Prefer an image from NVIDIA's official Jetson developer resources rather than an arbitrary third-party image.

Because Jetson Nano support is tied to specific JetPack/L4T releases, select the latest **appropriate supported Nano release**, not necessarily the latest JetPack available for newer Jetson hardware.

If NVIDIA's available Nano image uses an older Ubuntu/Python stack, that is acceptable.

The Compute Engine should abstract the underlying age of the operating system.

The important question is:

> Can the node reliably provide the BiblionOCR compute capabilities we need?

not:

> Is the operating system fashionable?

---

# 24. Windows Image-Burning Workflow

A practical Windows procedure is:

1. Download the appropriate NVIDIA Jetson Nano image.
2. Verify its checksum if NVIDIA provides one.
3. Decompress the archive using a trusted Windows decompression utility.
4. Identify the intended target storage device very carefully.
5. Use a reputable disk-imaging utility capable of writing the image correctly.
6. Verify the write if the imaging utility supports verification.
7. Safely eject the media.

**Be extremely careful about drive selection.**

A raw disk image operation can destroy the contents of the wrong disk.

Do not proceed until the target SSD/storage device is unambiguously identified.

---

# 25. First Headless Boot

After installing the new image:

1. Connect Ethernet if possible.
2. Boot the Nano.
3. Allow sufficient time for first boot initialization.
4. Determine its DHCP address from the router/network.
5. Connect using SSH.
6. Complete package updates appropriate to the selected NVIDIA release.
7. Verify CUDA and Jetson hardware.
8. Configure hostname.
9. Configure SSH keys.
10. Disable unnecessary graphical services if the chosen image installed them.
11. Confirm the node remains reachable after reboot.

The desired end state is:

```text
Windows:
    used for image preparation

Ubuntu 24 desktop:
    development/orchestration

Jetson:
    headless compute worker
```

---

# 26. Headless Does Not Mean "Barely Functional"

Keep enough of the NVIDIA stack to support:

- CUDA
- GPU diagnostics
- required runtime libraries
- Python environment
- networking
- SSH
- system monitoring

Remove unnecessary desktop applications only after the base system is proven stable.

A conservative minimalism is preferable to aggressive stripping.

---

# 27. BiblionOCR Agent Should Come Later

Once the Jetson is stable:

```text
Jetson OS
   |
NVIDIA stack
   |
Python environment
   |
BiblionOCR Compute Agent
   |
CUDA provider
   |
Network registration
```

The agent should not initially attempt sophisticated scheduling.

Its first job is simply:

> **Tell BiblionOCR what this machine is and whether it is available.**

Then we can add:

- workload reception
- health checks
- resource monitoring
- CUDA task execution
- result reporting
- failure reporting

---

# 28. Initial Compute Agent Protocol

A minimal first registration could eventually resemble:

```json
{
  "node": "nano-01",
  "architecture": "aarch64",
  "os": "ubuntu",
  "cuda": true,
  "gpu": {
    "vendor": "nvidia",
    "memory_mb": 4096
  },
  "capabilities": [
    "image_preprocessing",
    "feature_extraction",
    "lightweight_inference"
  ],
  "status": "online"
}
```

This is illustrative, not the final protocol.

The actual implementation should emerge from the Compute Engine architecture rather than being prematurely locked into JSON or a particular network framework.

---

# 29. Fallback and Bailout Are First-Class Features

A workload should never silently disappear because the preferred resource is unavailable.

Possible states:

```text
READY
QUEUED
RUNNING
COMPLETED
DEGRADED
DEFERRED
FAILED
REQUIRES_HUMAN
```

A useful distinction is:

### FAILED

The system attempted the operation and encountered an error.

### DEGRADED

The preferred resource was unavailable, but an acceptable fallback completed the task.

### DEFERRED

The system cannot safely execute the task now but expects that it may become executable later.

### REQUIRES_HUMAN

The system cannot make a sufficiently reliable decision and explicitly asks for human intervention.

That last state is especially important for computational humanities.

---

# 30. Governing Principle

The emerging architectural principle is:

> **BiblionOCR should be ambitious about computation and conservative about conclusions.**

It should use available intelligence aggressively for:

- classification
- recommendation
- optimization
- anomaly detection
- preprocessing selection
- resource selection

But it should remain conservative about:

- interpretation
- provenance
- scholarly assertions
- irreversible transformations
- unsupported inference

---

# 31. Immediate Next Steps

Do not implement all of this at once.

Recommended sequence:

### Phase 1 — Nano preservation and identification

- inventory current Nano
- determine exact JetPack/L4T version
- back up current installation
- identify exact Nano model/storage configuration

### Phase 2 — Headless base system

- select appropriate NVIDIA-supported Nano image
- write image from Windows
- boot headlessly
- establish SSH
- verify CUDA
- establish stable network identity

### Phase 3 — Compute Engine foundation

Extend the existing Compute Engine architecture with:

- resource registry
- capability states
- workload requirements
- fallback rules

### Phase 4 — Nano compute agent

Implement:

- registration
- heartbeat
- capability reporting
- resource monitoring
- basic work reception
- result reporting

### Phase 5 — First CUDA workload

Start with a narrowly defined workload such as:

- image preprocessing
- feature extraction
- lightweight inference

Do not begin with model training or a generalized AI service.

### Phase 6 — Intelligent workflow

Add a first ML-assisted decision:

```text
document/page characteristics
            |
            v
   preprocessing selector
            |
            v
     recommended strategy
            |
            v
      workflow engine
```

Record the recommendation and its provenance.

### Phase 7 — Learning loop

Only after the deterministic pipeline works:

```text
recommendation
      |
human result
      |
outcome recorded
      |
model evaluation
      |
improved recommendation
```

---

# 32. Final Architectural Picture

The direction now looks like this:

```text
                         BIBLIONOCR
                              |
        +---------------------+---------------------+
        |                     |                     |
        v                     v                     v
   WORKFLOW ENGINE      INTELLIGENCE LAYER    PROJECT KNOWLEDGE
        |                     |                     |
        +---------------------+---------------------+
                              |
                       COMPUTE ENGINE
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
         RESOURCE         CAPABILITY       MONITORING
         DISCOVERY         KNOWLEDGE
              |               |               |
              +---------------+---------------+
                              |
                       WORKLOAD PLANNER
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
          LOCAL CPU       LOCAL GPU       NETWORK NODE
                                              |
                                              v
                                         JETSON NANO
                                              |
                                             CUDA
                                              |
                                              v
                                         ML WORKLOAD
                                              |
                                              v
                                      RESULT + PROVENANCE
                                              |
                                              v
                                        WORKFLOW ENGINE
                                              |
                                      +-------+-------+
                                      |               |
                                      v               v
                                  AUTOMATE        HUMAN
                                                  BAILOUT
```

This is the direction that gives the Digital Humanities proposition real technical substance.

The objective is not to make BiblionOCR "AI-powered."

The objective is to make it **computationally intelligent, resource-aware, provenance-conscious, reproducible, and gracefully human when computation reaches its limits.**

That is a much more interesting thing to build.
