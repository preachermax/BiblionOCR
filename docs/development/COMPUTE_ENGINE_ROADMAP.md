# BiblionOCR Compute Engine Roadmap

Status: Architectural roadmap
Purpose: Preserve Compute Engine direction while implementation evolves through the module-by-module workflow.

## 1. Purpose

The Compute Engine discovers, characterizes, monitors, and allocates computational resources available to BiblionOCR.

It does not aim to become a general-purpose distributed-computing platform.

Primary question:

> What resources are available, what can they safely do for BiblionOCR, and where should a workload execute?

## 2. Governing Principle

BiblionOCR should be ambitious about computation and conservative about conclusions.

Machine intelligence can assist with:

- preprocessing
- classification
- feature extraction
- similarity analysis
- embeddings
- anomaly detection
- ML inference
- workflow optimization
- resource selection
- learned recommendations

It must remain conservative with:

- scholarly interpretation
- provenance integrity
- unsupported inference
- irreversible transformations
- authoritative conclusions

## 3. Core Responsibilities

### 3.1 Resource Discovery

Discover resources factually:

- local CPU
- local memory
- local storage
- local GPU
- CUDA and relevant runtimes
- network compute nodes

### 3.2 Capability Knowledge

Translate facts into BiblionOCR-relevant capabilities.

The knowledge layer answers:

> Can this resource execute this workload safely and efficiently?

### 3.3 Resource Monitoring

Track decision-relevant runtime state:

- availability
- CPU load
- memory pressure
- GPU availability and memory
- workload status
- node health
- failures

### 3.4 Workload Planning

Select execution path based on:

- workload requirements
- available resources
- capability knowledge
- current runtime state
- priority

### 3.5 Fallback and Bailout

Every non-mandatory accelerated workflow requires a safe fallback path.

```text
Preferred GPU
      |
      v
Alternate GPU
      |
      v
CPU
      |
      v
Deferred
      |
      v
Human intervention
```

## 4. Capability States

Use explicit capability states:

```text
KNOWN_GOOD        -> may use
KNOWN_UNSUITABLE  -> do not use
UNKNOWN           -> conservative fallback
```

Unknown must never be treated as implicitly available.

## 5. Bounded Knowledge Base

The knowledge base remains intentionally bounded and workload-oriented.

Do not turn it into:

- full vendor GPU catalog
- universal CUDA matrix
- cloud provider catalog
- generalized model registry

Illustrative shape:

```yaml
resource:
  vendor: NVIDIA
  architecture: Maxwell
  memory_mb: 4096

runtime:
  cuda: available

capabilities:
  image_preprocessing: true
  feature_extraction: true
  lightweight_inference: true

constraints:
  large_model_inference: restricted
```

## 6. Facts Versus Interpretation

Maintain a clear separation.

Discovered facts:

```text
Architecture: AARCH64
GPU: NVIDIA
GPU Memory: 4096 MB
CUDA: Available
Python: 3.x
```

BiblionOCR interpretation:

```text
Image preprocessing: suitable
Lightweight inference: suitable
Large-model inference: unsuitable
Training: restricted
```

The machine reports facts. The Compute Engine interprets facts.

## 7. CUDA as a Provider

CUDA is a provider capability, not the architectural foundation.

Preferred abstraction:

```text
Workload -> Capability Requirement -> Compute Engine -> Provider Selection
                                                 -> CPU / CUDA / Remote / Other
```

## 8. Remote Node Model

Remote nodes are compute resources, not remote desktops.

The Jetson Nano is the first intended resource type.

Expected node services:

- registration
- capability reporting
- heartbeat
- workload reception
- execution
- result reporting
- failure reporting

## 9. Workflow States

Target compute-aware workflow states:

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

Interpretation:

- FAILED: attempted and failed.
- DEGRADED: fallback succeeded.
- DEFERRED: not safe now; may become executable later.
- REQUIRES_HUMAN: insufficient confidence for autonomous action.

## 10. Architectural Boundaries

- Compute Engine does not own scholarship.
- Workflow Engine does not own hardware.
- Intelligence layer does not own compute.
- Providers do not own application logic.
- Remote nodes do not become remote desktops.
- ML recommendations do not become scholarly conclusions.

## 11. What This Should Not Become

Avoid expansion into:

- Kubernetes or cluster orchestration
- generalized cloud provisioning
- universal hardware abstraction
- autonomous scholarly interpretation

## 12. Development Coordination Rule

Compute Engine roadmap work must not interrupt module-by-module delivery.

Module flow remains:

```text
Prompt Pack -> Implementation -> Checklist -> Review -> Commit -> Resync
```

Use architecture checkpoints only when a module change requires compute, CUDA, ML, or fallback design decisions.

## 13. Phased Roadmap

### Phase 1 - Preserve current module workflow

Continue existing module delivery cadence.

### Phase 2 - Stabilize constraints

Formalize:

- discovery boundaries
- capability states
- workload requirements
- fallback rules
- remote-node principles
- provenance expectations

### Phase 3 - Nano preparation

Before image replacement:

1. inventory current Nano
2. confirm JetPack/L4T lineage
3. confirm storage/boot configuration
4. backup current installation
5. select NVIDIA-supported release
6. establish stable headless base and SSH
7. verify CUDA

### Phase 4 - Resource registry

Implement minimum useful registry for:

- local CPU
- local GPU
- remote Jetson
- capability state
- online/offline state

### Phase 5 - Nano compute agent

Implement:

- registration
- heartbeat
- capability reporting
- monitoring
- basic workload reception
- result reporting

### Phase 6 - First measurable CUDA workload

Start with one bounded workload:

- image preprocessing
- feature extraction
- lightweight inference

Measure CPU vs CUDA objectively before policy decisions.

### Phase 7 - Workload planner

Introduce:

- requirements matching
- resource selection
- fallback/degradation
- bailout

### Phase 8 - ML-assisted workflow

Ship one measurable recommendation path, then record outcomes.

### Phase 9 - Learning loop

Only after deterministic and ML-assisted paths are stable:

```text
Recommendation -> Human result -> Outcome record -> Evaluation -> Improved model
```

## 14. Decision Rules

1. Discover before assuming.
2. Capabilities are workload-oriented.
3. Unknown means conservative fallback.
4. Optional acceleration must not become hidden dependency.
5. CUDA is provider, not architecture.
6. Remote machines are compute resources, not remote desktops.
7. Keep knowledge base intentionally bounded.
8. Workloads describe requirements; hardware satisfies them.
9. Automated recommendations should be provenance-capable.
10. Human bailout is legitimate workflow state.
11. Do not build a general distributed-computing platform.
12. Keep ML recommendation separate from scholarly conclusion.
13. Prefer measurable capability over fashionable terminology.
14. Do not optimize for hardware/workloads you do not have.
15. Let real BiblionOCR workloads teach architecture.

## 15. Current Decision

Continue module-by-module implementation.

Develop Compute Engine as a parallel architectural track and convert mature constraints into bounded implementation tasks through the existing Prompt Pack and checklist workflow.
