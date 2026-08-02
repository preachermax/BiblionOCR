# COMPUTE_ENGINE_ARCHITECTURE.md

# BiblionOCR Compute Engine Architecture

**Status:** Planning
**Revision:** 0.1
**Project:** BiblionOCR

---

# Purpose

The Compute Engine is responsible for discovering, profiling, monitoring, and utilizing all available computational resources available to BiblionOCR.

The objective is not merely to detect CUDA devices, but to provide a unified abstraction layer through which every hardware accelerator may be discovered and leveraged by the application.

This architecture intentionally extends beyond the current implementation of Tesseract OCR and is designed to support future AI, OCR, and image-processing workloads.

---

# Design Philosophy

The Compute Engine treats all computational resources as discoverable services.

Hardware should never be hard-coded into application logic.

Instead, every subsystem should request computational capabilities from the Compute Engine rather than interacting directly with individual hardware APIs.

---

# Architectural Goals

The Compute Engine shall:

* Discover available hardware.
* Profile system capabilities.
* Monitor computational resources.
* Allocate workloads.
* Provide a unified interface to software modules.
* Support future expansion without architectural redesign.

---

# Responsibilities

The Compute Engine is responsible for:

## Hardware Discovery

* CPU
* Memory
* Storage
* GPU(s)
* CUDA devices
* OpenCL devices
* External accelerators
* Future AI hardware

---

## Capability Discovery

Determine available software support including:

* CUDA Runtime
* cuDNN
* TensorRT
* OpenCV CUDA
* OpenCL
* ONNX Runtime
* Future inference engines

---

## Resource Monitoring

Monitor:

* CPU utilization
* GPU utilization
* Memory usage
* VRAM
* Storage capacity
* Temperature
* Power status (where supported)

---

## Workload Scheduling

Provide intelligent workload assignment for:

* OCR preprocessing
* Image enhancement
* Dataset generation
* AI inference
* Model training
* Benchmarking

---

# Proposed Directory Structure

```
Developer/
    hardware/
        detector.py
        cpu.py
        gpu.py
        cuda.py
        opencl.py
        memory.py
        storage.py
        benchmark.py

Core/
    compute_engine.py
```

---

# Hardware Discovery

The Compute Engine should identify:

* CPU manufacturer
* CPU model
* Core count
* Thread count

Memory:

* Installed RAM
* Available RAM

Storage:

* Capacity
* Available space
* Device type

GPU(s):

* Vendor
* Model
* Driver version
* Compute capability
* VRAM

---

# Capability Discovery

Hardware alone is insufficient.

The Compute Engine should determine software capabilities.

Examples include:

* CUDA installed
* CUDA version
* cuDNN installed
* TensorRT installed
* OpenCV CUDA support
* OpenCL support
* ONNX Runtime
* Additional AI frameworks

---

# Hardware Profile

The Compute Engine shall generate a hardware profile similar to:

```json
{
    "cpu": {
        "model": "...",
        "cores": 8
    },

    "memory": {
        "installed_gb": 32
    },

    "cuda": {
        "available": true,
        "version": "12.x"
    },

    "gpus": [
        {
            "vendor": "NVIDIA",
            "model": "Jetson Nano",
            "cuda": true
        }
    ]
}
```

This profile becomes the authoritative hardware description for the current runtime.

Current implementation note:

* `Core/compute_profile.py` now defines schema-only dataclasses for the normalized profile shape: `CPUProfile`, `MemoryProfile`, `StorageProfile`, `OSProfile`, `PythonProfile`, `GPUProfile`, `CUDAProfile`, `ProviderProfileEntry`, and `HardwareProfile`
* the refinement pass keeps storage and memory capacities in bytes, names CPU topology fields as `physical_cores` and `logical_cores`, and reserves `HardwareProfile.raw` for provider-native diagnostic payloads
* this file intentionally contains no discovery, registration, monitoring, or aggregation logic
* provider implementations and `ComputeEngine` output are not yet wired to these dataclasses; they remain a type-definition layer only

---

# Tesseract Training

Current versions of Tesseract perform LSTM training primarily on the CPU.

Consequently, CUDA should not be expected to directly accelerate the Tesseract training engine.

Instead, the Compute Engine should accelerate the stages surrounding OCR training.

These include:

* Image preprocessing
* Adaptive thresholding
* Denoising
* Morphological operations
* Deskewing
* Segmentation
* Dataset preparation

Improved preprocessing increases training quality while leveraging available GPU resources.

---

# Processing Pipeline

```
Images

↓

Compute Engine

↓

GPU-Accelerated Preprocessing

↓

OCR Dataset Builder

↓

Tesseract Training

↓

Validation

↓

Model Packaging
```

---

# GPU Discovery Strategy

The Compute Engine should support multiple accelerator providers.

Initial targets include:

* NVIDIA CUDA
* OpenCL
* Intel oneAPI
* AMD ROCm
* Apple Metal (future)
* Software fallback

Each provider should expose a common interface describing:

* Availability
* Supported features
* Performance characteristics

---

# Jetson Support

Jetson-specific discovery should include:

* JetPack version
* CUDA Runtime
* TensorRT
* OpenCV CUDA
* GPU characteristics
* tegrastats monitoring

Where available:

* nvidia-smi

---

# External GPU Support

The architecture shall support multiple simultaneous accelerators including:

* Internal GPU
* External GPU
* Thunderbolt GPU
* PCIe GPU
* USB AI accelerators
* Future hardware

Multiple accelerators should appear as independent compute resources managed by the Compute Engine.

---

# Developer Services Integration

Future versions of Developer Services should expose a Compute Dashboard displaying:

* CPU utilization
* GPU utilization
* Memory
* VRAM
* Active workloads
* CUDA status
* OpenCL status
* Benchmark results
* Training queue

This dashboard should become part of the observable runtime architecture.

---

# Proposed Development Milestones

## v1.9

* Hardware discovery
* JSON hardware profile
* CPU
* Memory
* Storage

---

## v2.0

* GPU discovery
* CUDA discovery
* Capability graph
* Developer Services integration

---

## v2.1

* CUDA-accelerated preprocessing
* Benchmark framework
* Performance profiling

---

## v2.2

* OCR dataset builder
* Training manager
* Model packaging
* Validation pipeline

---

## v2.3

* Multi-GPU scheduling
* Remote compute support
* Distributed training
* Future AI accelerators

---

# Long-Term Vision

The Compute Engine shall become the centralized computational subsystem of BiblionOCR.

Rather than serving only Tesseract OCR, it will provide a unified architecture through which current and future OCR engines, AI models, image-processing pipelines, benchmarking tools, and hardware accelerators may operate.

The Compute Engine is intended to remain hardware-agnostic, extensible, and observable, ensuring that BiblionOCR can evolve alongside emerging computational technologies without requiring fundamental architectural redesign.

---

*"Making systems visible extends beyond software—it includes the computational resources that bring those systems to life."*
