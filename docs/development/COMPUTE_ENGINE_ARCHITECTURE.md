# BiblionOCR Compute Engine Architecture Contract

Status: Implementation contract
Revision: 0.2
Scope: Runtime-facing architecture contract for compute discovery, profiling, status, and provider abstraction.

## 1. Purpose

Define what the current Compute Engine must guarantee to callers and where future extensions should attach.

This contract intentionally separates:

- current implemented behavior
- emerging implementation direction
- planned capabilities

## 2. Current Runtime Surface

### 2.1 ComputeEngine API

Current public orchestration lives in Core/compute_engine.py and provides:

- provider registration/unregistration
- provider discovery/bootstrap
- availability filtering
- normalized profile aggregation
- normalized status aggregation

### 2.2 Provider Registry

Current provider lifecycle management in Core/compute_registry.py provides:

- in-memory provider set
- idempotent registration
- safe unregistration
- one-time bootstrap discovery

### 2.3 Provider Contract

Core/compute_provider.py defines the provider interface:

- available() -> bool
- profile() -> Mapping[str, Any]
- status() -> Mapping[str, Any]

Providers own platform-specific logic.

### 2.4 Profile Schema Layer

Core/compute_profile.py currently defines schema dataclasses.

Important constraint:

- schema definitions exist
- runtime aggregation is not yet fully wired to dataclass serialization

## 3. Normalized Output Contract

ComputeEngine returns stable top-level sections for profile and status payloads.

Required sections:

- cpu
- memory
- storage
- gpus
- cuda
- providers

Design intent:

- callers consume stable top-level keys
- provider-native detail remains available through provider payload sections

## 4. Architectural Constraints

1. ComputeEngine must not embed hardware-specific heuristics.
2. Provider implementations must encapsulate platform logic.
3. Callers should request capability through ComputeEngine, not direct hardware APIs.
4. CPU-only execution must remain valid baseline behavior.
5. CUDA support is additive capability, not mandatory dependency.

## 5. Capability Model Direction

Capability semantics should become workload-oriented and explicit.

Target capability states:

- KNOWN_GOOD
- KNOWN_UNSUITABLE
- UNKNOWN

Unknown implies conservative fallback.

## 6. Workload Planning Direction

Workload planner is not yet first-class in runtime, but architecture requires:

- workload requirement declaration
- capability matching
- resource preference order
- fallback and degradation paths
- explicit human bailout state

## 7. Jetson and Remote Node Direction

Remote node model (including Jetson Nano) should be treated as provider/resource integration, not remote desktop automation.

Target remote-node primitives:

- registration
- heartbeat
- capability report
- workload reception
- result and failure reporting

## 8. Non-Goals

Compute Engine is not intended to become:

- cluster orchestrator
- cloud provisioning platform
- generalized distributed-training framework
- universal hardware encyclopedia

## 9. Integration Expectations

Compute-aware module code should:

1. request capability from ComputeEngine
2. avoid direct accelerator coupling where shared provider abstraction exists
3. preserve deterministic fallback behavior when acceleration unavailable

## 10. Versioned Adoption Path

### Near term

- stabilize provider discovery and normalized output
- validate provider payload consistency
- expose status/profile surfaces to diagnostics tooling

### Mid term

- introduce minimal resource registry semantics
- add workload requirement descriptions
- formalize fallback/degradation state transitions

### Later

- add remote node provider support
- add bounded Jetson compute-agent integration
- add first measurable CUDA-backed workload path

## 11. Relationship to Roadmap

Strategy and sequencing live in docs/development/COMPUTE_ENGINE_ROADMAP.md.

This file is the implementation contract that keeps runtime behavior constrained while the roadmap evolves.
