from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class CPUProfile:
	vendor: str | None = None
	model: str | None = None
	architecture: str | None = None
	platform: str | None = None
	physical_cores: int | None = None
	logical_cores: int | None = None


@dataclass
class MemoryProfile:
	installed_bytes: int | None = None
	total_bytes: int | None = None
	available_bytes: int | None = None


@dataclass
class StorageProfile:
	path: str | None = None
	capacity_bytes: int | None = None
	total_bytes: int | None = None
	available_bytes: int | None = None
	free_bytes: int | None = None
	used_bytes: int | None = None


@dataclass
class OSProfile:
	name: str | None = None
	version: str | None = None
	release: str | None = None
	platform: str | None = None
	architecture: str | None = None


@dataclass
class PythonProfile:
	implementation: str | None = None
	version: str | None = None
	executable: str | None = None
	prefix: str | None = None
	virtualenv: bool | None = None


@dataclass
class GPUProfile:
	vendor: str | None = None
	model: str | None = None
	bus_id: str | None = None
	driver_version: str | None = None
	memory_total_mb: int | None = None


@dataclass
class CUDAProfile:
	available: bool = False
	version: str | None = None
	device_count: int = 0
	devices: List[GPUProfile] = field(default_factory=list)
	driver_version: str | None = None
	cuda_home: str | None = None
	nvcc_path: str | None = None
	runtime_library: str | None = None
	jetpack_version: str | None = None


@dataclass
class ProviderProfileEntry:
	provider: str | None = None
	available: bool = False
	profile: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HardwareProfile:
	cpu: CPUProfile = field(default_factory=CPUProfile)
	memory: MemoryProfile = field(default_factory=MemoryProfile)
	storage: StorageProfile = field(default_factory=StorageProfile)
	os: OSProfile = field(default_factory=OSProfile)
	python: PythonProfile = field(default_factory=PythonProfile)
	gpus: List[GPUProfile] = field(default_factory=list)
	cuda: CUDAProfile = field(default_factory=CUDAProfile)
	providers: List[ProviderProfileEntry] = field(default_factory=list)
	available_providers: List[str] = field(default_factory=list)
	raw: Dict[str, Any] = field(default_factory=dict)


__all__ = [
	"CPUProfile",
	"MemoryProfile",
	"StorageProfile",
	"OSProfile",
	"PythonProfile",
	"GPUProfile",
	"CUDAProfile",
	"ProviderProfileEntry",
	"HardwareProfile",
]
