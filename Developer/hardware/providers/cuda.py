from __future__ import annotations

import ctypes.util
import glob
import json
import os
import platform
import re
import shutil
import subprocess
from typing import Any, Dict, Iterable, Mapping

from Core.compute_provider import ComputeProvider


class CUDAProvider(ComputeProvider):
	"""Provide CUDA runtime and device metadata when CUDA is available."""

	def available(self) -> bool:
		"""Return whether a CUDA runtime or toolkit appears to be available."""
		summary = self._summary()
		return bool(summary["available"])

	def profile(self) -> Mapping[str, Any]:
		"""Return descriptive CUDA runtime and device information."""
		summary = self._summary()

		return {
			"resource": "cuda",
			"available": summary["available"],
			"version": summary["version"],
			"cuda_home": summary["cuda_home"],
			"nvcc_path": summary["nvcc_path"],
			"device_count": len(summary["devices"]),
			"devices": summary["devices"],
		}

	def status(self) -> Mapping[str, Any]:
		"""Return current CUDA runtime visibility and device status."""
		summary = self._summary()

		return {
			"resource": "cuda",
			"available": summary["available"],
			"version": summary["version"],
			"driver_version": summary["driver_version"],
			"device_count": len(summary["devices"]),
			"devices": summary["devices"],
		}

	def _summary(self) -> Dict[str, Any]:
		"""Build a normalized CUDA runtime summary."""
		devices = self._nvidia_smi_devices()
		version = (
			self._cuda_version_from_nvidia_smi()
			or self._cuda_version_from_nvcc()
			or self._cuda_version_from_file()
		)
		cuda_home = self._cuda_home()
		nvcc_path = shutil.which("nvcc")
		runtime_library = self._runtime_library()
		jetpack_version = self._jetpack_version()
		driver_version = devices[0].get("driver_version") if devices else None

		return {
			"available": bool(version or devices or cuda_home or nvcc_path or runtime_library),
			"version": version,
			"cuda_home": cuda_home,
			"nvcc_path": nvcc_path,
			"runtime_library": runtime_library,
			"jetpack_version": jetpack_version,
			"driver_version": driver_version,
			"devices": devices,
		}

	def _nvidia_smi_devices(self) -> tuple[Dict[str, Any], ...]:
		"""Read CUDA-capable device information from nvidia-smi when available."""
		output = self._run_command(
			(
				"nvidia-smi",
				"--query-gpu=name,pci.bus_id,driver_version,memory.total",
				"--format=csv,noheader,nounits",
			)
		)
		if output is None:
			return ()

		devices = []
		for line in output.splitlines():
			parts = [part.strip() for part in line.split(",")]
			if len(parts) != 4:
				continue

			devices.append(
				{
					"vendor": "NVIDIA",
					"model": parts[0],
					"bus_id": parts[1],
					"driver_version": parts[2],
					"memory_total_mb": self._to_int(parts[3]),
				}
			)

		return tuple(devices)

	def _cuda_version_from_nvidia_smi(self) -> str | None:
		"""Parse the CUDA version banner from nvidia-smi output."""
		output = self._run_command(("nvidia-smi",))
		if output is None:
			return None

		return self._parse_nvidia_smi_cuda_version(output)

	def _cuda_version_from_nvcc(self) -> str | None:
		"""Parse the CUDA version from nvcc output when nvcc is present."""
		output = self._run_command(("nvcc", "--version"))
		if output is None:
			return None

		return self._parse_nvcc_version(output)

	def _cuda_version_from_file(self) -> str | None:
		"""Read a CUDA version from toolkit metadata files when present."""
		for candidate in self._cuda_version_file_candidates():
			if candidate.endswith(".json"):
				version = self._cuda_version_from_json(candidate)
			else:
				version = self._cuda_version_from_text_file(candidate)

			if version is not None:
				return version

		return None

	def _cuda_version_file_candidates(self) -> tuple[str, ...]:
		"""Return candidate CUDA metadata files to inspect."""
		candidates = []
		cuda_home = self._cuda_home()

		if cuda_home is not None:
			candidates.extend(
				[
					os.path.join(cuda_home, "version.json"),
					os.path.join(cuda_home, "version.txt"),
				]
			)

		candidates.extend(
			[
				"/usr/local/cuda/version.json",
				"/usr/local/cuda/version.txt",
			]
		)

		if platform.system() == "Windows":
			candidates.extend(glob.glob(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*\version.json"))
			candidates.extend(glob.glob(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*\version.txt"))

		return tuple(dict.fromkeys(candidates))

	def _cuda_version_from_json(self, path: str) -> str | None:
		"""Parse a CUDA version from a version.json file."""
		try:
			with open(path, "r", encoding="utf-8") as handle:
				payload = json.load(handle)
		except (OSError, ValueError):
			return None

		cuda_payload = payload.get("cuda") if isinstance(payload, dict) else None
		if isinstance(cuda_payload, dict):
			version = cuda_payload.get("version")
			return str(version) if version else None

		version = payload.get("version") if isinstance(payload, dict) else None
		return str(version) if version else None

	def _cuda_version_from_text_file(self, path: str) -> str | None:
		"""Parse a CUDA version from a version.txt file."""
		try:
			with open(path, "r", encoding="utf-8") as handle:
				contents = handle.read()
		except OSError:
			return None

		match = re.search(r"CUDA Version\s*([0-9]+(?:\.[0-9]+)*)", contents)
		if match is not None:
			return match.group(1)

		match = re.search(r"([0-9]+(?:\.[0-9]+)+)", contents)
		return None if match is None else match.group(1)

	def _cuda_home(self) -> str | None:
		"""Return the configured CUDA home directory when present."""
		for environment_variable in ("CUDA_HOME", "CUDA_PATH"):
			value = os.environ.get(environment_variable)
			if value:
				return value

		default_path = "/usr/local/cuda"
		if os.path.isdir(default_path):
			return default_path

		if platform.system() == "Windows":
			matches = sorted(glob.glob(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*"))
			if matches:
				return matches[-1]

		return None

	def _runtime_library(self) -> str | None:
		"""Return the resolved CUDA runtime library name when discoverable."""
		for library_name in ("cuda", "nvcuda"):
			resolved = ctypes.util.find_library(library_name)
			if resolved:
				return resolved

		return None

	def _jetpack_version(self) -> str | None:
		"""Return the JetPack/L4T release version on Jetson platforms."""
		try:
			with open("/etc/nv_tegra_release", "r", encoding="utf-8") as handle:
				contents = handle.read()
		except OSError:
			return None

		return self._parse_jetpack_version(contents)

	def _parse_jetpack_version(self, contents: str) -> str | None:
		"""Parse an L4T / JetPack release string from nv_tegra_release text."""
		match = re.search(r"R([0-9]+)\s*\(release\),\s*REVISION:\s*([0-9.]+)", contents)
		if match is None:
			return contents.strip() or None

		return f"L4T R{match.group(1)}.{match.group(2)}"

	def _run_command(self, command: Iterable[str]) -> str | None:
		"""Run a shell command and return stdout when it succeeds."""
		try:
			result = subprocess.run(
				tuple(command),
				check=False,
				capture_output=True,
				text=True,
			)
		except OSError:
			return None

		if result.returncode != 0:
			return None

		return result.stdout.strip() or None

	def _parse_nvcc_version(self, output: str) -> str | None:
		"""Parse a CUDA version from nvcc --version output."""
		match = re.search(r"release\s+([0-9]+(?:\.[0-9]+)*)", output)
		return None if match is None else match.group(1)

	def _parse_nvidia_smi_cuda_version(self, output: str) -> str | None:
		"""Parse a CUDA version from the nvidia-smi banner."""
		match = re.search(r"CUDA Version:\s*([0-9]+(?:\.[0-9]+)*)", output)
		return None if match is None else match.group(1)

	def _to_int(self, value: str) -> int | None:
		"""Convert integer-like strings to integers."""
		try:
			return int(value)
		except ValueError:
			return None