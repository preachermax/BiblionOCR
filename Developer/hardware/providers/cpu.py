from __future__ import annotations

import os
import platform
from typing import Any, Dict, Mapping

from Core.compute_provider import ComputeProvider


class CPUProvider(ComputeProvider):
	"""Provide CPU profile and runtime status information."""

	def available(self) -> bool:
		"""Return whether CPU information is available to the runtime."""
		return self._logical_threads() is not None

	def profile(self) -> Mapping[str, Any]:
		"""Return descriptive CPU metadata for the current runtime."""
		vendor, model = self._cpu_identity()

		return {
			"resource": "cpu",
			"vendor": vendor,
			"model": model,
			"architecture": platform.machine() or None,
			"platform": platform.system() or None,
			"logical_threads": self._logical_threads(),
		}

	def status(self) -> Mapping[str, Any]:
		"""Return current CPU runtime status for the current process host."""
		load_average = self._load_average()

		return {
			"resource": "cpu",
			"logical_threads": self._logical_threads(),
			"load_average_1m": load_average[0],
			"load_average_5m": load_average[1],
			"load_average_15m": load_average[2],
		}

	def _cpu_identity(self) -> tuple[str | None, str | None]:
		"""Return vendor and model information when available."""
		vendor = None
		model = None

		try:
			with open("/proc/cpuinfo", "r", encoding="utf-8") as handle:
				for line in handle:
					if ":" not in line:
						continue

					key, value = [part.strip() for part in line.split(":", 1)]

					if key == "vendor_id" and vendor is None:
						vendor = value or None
					elif key == "model name" and model is None:
						model = value or None

					if vendor is not None and model is not None:
						break
		except OSError:
			pass

		if model is None:
			model = platform.processor() or None

		return vendor, model

	def _logical_threads(self) -> int | None:
		"""Return the logical thread count reported by the runtime."""
		return os.cpu_count()

	def _load_average(self) -> tuple[float | None, float | None, float | None]:
		"""Return host load averages when the platform supports them."""
		try:
			return os.getloadavg()
		except (AttributeError, OSError):
			return (None, None, None)