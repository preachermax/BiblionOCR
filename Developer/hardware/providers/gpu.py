from __future__ import annotations

import csv
import glob
import json
import os
import platform
import re
import subprocess
from typing import Any, Dict, Iterable, Mapping

from Core.compute_provider import ComputeProvider


class GPUProvider(ComputeProvider):
	"""Provide generic GPU inventory and runtime status information."""

	_DISPLAY_CLASSES = (
		"VGA compatible controller",
		"3D controller",
		"Display controller",
	)

	_VENDOR_NAMES = {
		"0x10de": "NVIDIA",
		"0x1002": "AMD",
		"0x1022": "AMD",
		"0x8086": "Intel",
	}

	def available(self) -> bool:
		"""Return whether one or more GPU devices can be identified."""
		return bool(self._devices())

	def profile(self) -> Mapping[str, Any]:
		"""Return descriptive GPU device metadata for the current host."""
		devices = self._devices()

		return {
			"resource": "gpu",
			"device_count": len(devices),
			"devices": devices,
		}

	def status(self) -> Mapping[str, Any]:
		"""Return current GPU runtime status for detected devices."""
		devices = self._devices()
		runtime_metrics = self._nvidia_runtime_metrics()

		return {
			"resource": "gpu",
			"device_count": len(devices),
			"devices": [self._merge_runtime_metrics(device, runtime_metrics) for device in devices],
			"runtime_metrics_supported": bool(runtime_metrics),
		}

	def _devices(self) -> tuple[Dict[str, Any], ...]:
		"""Return detected GPU devices using the best available source."""
		if platform.system() == "Windows":
			return self._devices_from_windows()

		devices = self._devices_from_lspci()
		if devices:
			return devices

		devices = self._devices_from_sysfs()
		if devices:
			return devices

		return self._devices_from_jetson_sysfs()

	def _devices_from_windows(self) -> tuple[Dict[str, Any], ...]:
		"""Read GPU information from Windows management interfaces."""
		output = self._run_first_available_command(
			(
				(
					"powershell",
					"-NoProfile",
					"-Command",
					"Get-CimInstance Win32_VideoController | Select-Object Name,AdapterCompatibility,DriverVersion,AdapterRAM,PNPDeviceID,VideoProcessor | ConvertTo-Json -Compress",
				),
				(
					"pwsh",
					"-NoProfile",
					"-Command",
					"Get-CimInstance Win32_VideoController | Select-Object Name,AdapterCompatibility,DriverVersion,AdapterRAM,PNPDeviceID,VideoProcessor | ConvertTo-Json -Compress",
				),
			)
		)
		if output is not None:
			devices = self._devices_from_windows_json(output)
			if devices:
				return devices

		output = self._run_command(
			(
				"wmic",
				"path",
				"win32_VideoController",
				"get",
				"Name,AdapterCompatibility,DriverVersion,AdapterRAM,PNPDeviceID,VideoProcessor",
				"/format:csv",
			)
		)
		if output is None:
			return ()

		return self._devices_from_wmic_csv(output)

	def _devices_from_lspci(self) -> tuple[Dict[str, Any], ...]:
		"""Read GPU information from lspci when it is available."""
		output = self._run_command(("lspci",))
		if output is None:
			return ()

		return self._devices_from_lspci_output(output)

	def _devices_from_lspci_output(self, output: str) -> tuple[Dict[str, Any], ...]:
		"""Parse GPU devices from lspci output for deterministic testing."""
		devices = []

		for line in output.splitlines():
			match = re.match(
				r"^(?P<bus>\S+)\s+(?P<class>VGA compatible controller|3D controller|Display controller):\s+(?P<description>.+)$",
				line.strip(),
			)
			if match is None:
				continue

			description = match.group("description")
			devices.append(
				{
					"vendor": self._vendor_from_description(description),
					"model": description,
					"class": match.group("class"),
					"bus_id": match.group("bus"),
				}
			)

		return tuple(devices)

	def _devices_from_sysfs(self) -> tuple[Dict[str, Any], ...]:
		"""Read GPU information from sysfs as a fallback when lspci is absent."""
		devices = []
		seen_paths = set()

		for device_path in sorted(glob.glob("/sys/class/drm/card*/device")):
			real_path = os.path.realpath(device_path)
			if real_path in seen_paths:
				continue

			seen_paths.add(real_path)
			vendor_id = self._read_text(os.path.join(real_path, "vendor"))
			device_id = self._read_text(os.path.join(real_path, "device"))
			uevent = self._read_key_value_file(os.path.join(real_path, "uevent"))
			driver = os.path.basename(os.path.realpath(os.path.join(real_path, "driver")))
			if driver == "driver":
				driver = None

			devices.append(
				{
					"vendor": self._vendor_name(vendor_id),
					"model": uevent.get("PCI_ID", device_id),
					"driver": driver,
					"bus_id": os.path.basename(real_path),
				}
			)

		return tuple(devices)

	def _devices_from_jetson_sysfs(self) -> tuple[Dict[str, Any], ...]:
		"""Read Jetson-integrated GPU information from device-tree backed sysfs."""
		devices = []

		for compatible_path in sorted(glob.glob("/sys/class/devfreq/*/device/of_node/compatible")):
			compatible = self._read_text(compatible_path)
			if compatible is None:
				continue

			compatible_values = [value for value in compatible.replace("\x00", "\n").splitlines() if value]
			if not any("nvidia" in value.lower() for value in compatible_values):
				continue

			device_root = os.path.dirname(os.path.dirname(compatible_path))
			name = self._read_text(os.path.join(device_root, "of_node", "name"))
			driver = os.path.basename(os.path.realpath(os.path.join(device_root, "driver")))
			if driver == "driver":
				driver = None

			devices.append(
				{
					"vendor": "NVIDIA",
					"model": self._jetson_model_name(name, compatible_values),
					"driver": driver,
					"platform": "jetson",
					"bus_id": os.path.basename(os.path.dirname(compatible_path)),
				}
			)

		return tuple(devices)

	def _devices_from_windows_json(self, output: str) -> tuple[Dict[str, Any], ...]:
		"""Parse GPU devices from PowerShell JSON output for deterministic testing."""
		try:
			payload = json.loads(output)
		except ValueError:
			return ()

		if isinstance(payload, dict):
			entries = [payload]
		elif isinstance(payload, list):
			entries = [entry for entry in payload if isinstance(entry, dict)]
		else:
			return ()

		devices = []
		for entry in entries:
			description = str(entry.get("Name") or entry.get("VideoProcessor") or "").strip()
			adapter_compatibility = str(entry.get("AdapterCompatibility") or "").strip()
			pnp_device_id = str(entry.get("PNPDeviceID") or "").strip()
			devices.append(
				{
					"vendor": self._windows_vendor_name(adapter_compatibility, description, pnp_device_id),
					"model": description or None,
					"driver_version": str(entry.get("DriverVersion") or "").strip() or None,
					"memory_total_mb": self._windows_memory_mb(entry.get("AdapterRAM")),
					"pnp_device_id": pnp_device_id or None,
				}
			)

		return tuple(devices)

	def _devices_from_wmic_csv(self, output: str) -> tuple[Dict[str, Any], ...]:
		"""Parse GPU devices from WMIC CSV output for deterministic testing."""
		rows = csv.DictReader(output.splitlines())
		devices = []

		for row in rows:
			description = str(row.get("Name") or row.get("VideoProcessor") or "").strip()
			adapter_compatibility = str(row.get("AdapterCompatibility") or "").strip()
			pnp_device_id = str(row.get("PNPDeviceID") or "").strip()
			if not description and not adapter_compatibility:
				continue

			devices.append(
				{
					"vendor": self._windows_vendor_name(adapter_compatibility, description, pnp_device_id),
					"model": description or None,
					"driver_version": str(row.get("DriverVersion") or "").strip() or None,
					"memory_total_mb": self._windows_memory_mb(row.get("AdapterRAM")),
					"pnp_device_id": pnp_device_id or None,
				}
			)

		return tuple(devices)

	def _nvidia_runtime_metrics(self) -> Dict[str, Dict[str, Any]]:
		"""Return runtime metrics keyed by GPU bus ID when nvidia-smi is available."""
		output = self._run_command(
			(
				"nvidia-smi",
				"--query-gpu=pci.bus_id,utilization.gpu,memory.used,memory.total,temperature.gpu",
				"--format=csv,noheader,nounits",
			)
		)
		if output is None:
			return {}

		metrics: Dict[str, Dict[str, Any]] = {}
		for line in output.splitlines():
			parts = [part.strip() for part in line.split(",")]
			if len(parts) != 5:
				continue

			bus_id = self._normalize_bus_id(parts[0])
			metrics[bus_id] = {
				"utilization_gpu_percent": self._to_int(parts[1]),
				"memory_used_mb": self._to_int(parts[2]),
				"memory_total_mb": self._to_int(parts[3]),
				"temperature_c": self._to_int(parts[4]),
			}

		return metrics

	def _merge_runtime_metrics(
		self,
		device: Dict[str, Any],
		runtime_metrics: Dict[str, Dict[str, Any]],
	) -> Dict[str, Any]:
		"""Merge optional runtime metrics into a device record."""
		merged = dict(device)
		bus_id = self._normalize_bus_id(str(device.get("bus_id", "")))
		merged.update(runtime_metrics.get(bus_id, {}))
		return merged

	def _vendor_from_description(self, description: str) -> str | None:
		"""Infer a vendor name from an lspci description."""
		vendor_markers = (
			("NVIDIA", "NVIDIA"),
			("AMD", "AMD"),
			("ATI", "AMD"),
			("Intel", "Intel"),
		)

		for marker, vendor in vendor_markers:
			if marker in description:
				return vendor

		return description.split()[0] if description else None

	def _vendor_name(self, vendor_id: str | None) -> str | None:
		"""Map a PCI vendor identifier to a human-readable vendor name."""
		if vendor_id is None:
			return None

		return self._VENDOR_NAMES.get(vendor_id.lower(), vendor_id)

	def _windows_vendor_name(
		self,
		adapter_compatibility: str,
		description: str,
		pnp_device_id: str,
	) -> str | None:
		"""Infer a Windows GPU vendor from multiple descriptive fields."""
		vendor = self._vendor_from_description(adapter_compatibility or description)
		if vendor is not None:
			return vendor

		match = re.search(r"VEN_([0-9A-Fa-f]{4})", pnp_device_id)
		if match is None:
			return None

		return self._vendor_name(f"0x{match.group(1).lower()}")

	def _windows_memory_mb(self, value: Any) -> int | None:
		"""Convert Windows adapter memory bytes to megabytes."""
		try:
			memory_bytes = int(str(value))
		except (TypeError, ValueError):
			return None

		if memory_bytes <= 0:
			return None

		return round(memory_bytes / (1024 ** 2))

	def _jetson_model_name(self, name: str | None, compatible_values: Iterable[str]) -> str:
		"""Build a readable Jetson GPU model name from sysfs values."""
		if name:
			return name

		compatible = next(iter(compatible_values), "jetson-gpu")
		return compatible.split(",")[-1]

	def _read_text(self, path: str) -> str | None:
		"""Read a trimmed text file when available."""
		try:
			with open(path, "r", encoding="utf-8") as handle:
				return handle.read().strip() or None
		except OSError:
			return None

	def _read_key_value_file(self, path: str) -> Dict[str, str]:
		"""Read simple KEY=VALUE files into a dictionary."""
		contents = self._read_text(path)
		if contents is None:
			return {}

		values = {}
		for line in contents.splitlines():
			if "=" not in line:
				continue

			key, value = line.split("=", 1)
			values[key] = value

		return values

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

	def _run_first_available_command(
		self,
		commands: Iterable[Iterable[str]],
	) -> str | None:
		"""Run the first available command that returns useful output."""
		for command in commands:
			output = self._run_command(command)
			if output is not None:
				return output

		return None

	def _normalize_bus_id(self, bus_id: str) -> str:
		"""Normalize GPU bus IDs so metrics can be merged consistently."""
		return bus_id.lower().replace("0000:", "")

	def _to_int(self, value: str) -> int | None:
		"""Convert integer-like strings to integers."""
		try:
			return int(value)
		except ValueError:
			return None