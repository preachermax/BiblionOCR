from __future__ import annotations

import os
from typing import Any, Dict, Mapping

from Core.compute_provider import ComputeProvider


class MemoryProvider(ComputeProvider):
	"""Provide system memory profile and runtime status information."""

	def available(self) -> bool:
		"""Return whether system memory information is available."""
		return self._memory_snapshot() is not None

	def profile(self) -> Mapping[str, Any]:
		"""Return descriptive memory capacity metadata for the host."""
		snapshot = self._memory_snapshot() or {}
		total_bytes = snapshot.get("total_bytes")

		return {
			"resource": "memory",
			"total_bytes": total_bytes,
			"total_gb": self._bytes_to_gb(total_bytes),
		}

	def status(self) -> Mapping[str, Any]:
		"""Return current memory availability and consumption data."""
		snapshot = self._memory_snapshot() or {}
		total_bytes = snapshot.get("total_bytes")
		available_bytes = snapshot.get("available_bytes")
		free_bytes = snapshot.get("free_bytes")
		used_bytes = None

		if total_bytes is not None and available_bytes is not None:
			used_bytes = total_bytes - available_bytes

		return {
			"resource": "memory",
			"total_bytes": total_bytes,
			"available_bytes": available_bytes,
			"free_bytes": free_bytes,
			"used_bytes": used_bytes,
		}

	def _memory_snapshot(self) -> Dict[str, int] | None:
		"""Return a normalized memory snapshot for the current host."""
		snapshot = self._linux_meminfo_snapshot()
		if snapshot is not None:
			return snapshot

		return self._sysconf_memory_snapshot()

	def _linux_meminfo_snapshot(self) -> Dict[str, int] | None:
		"""Read memory information from /proc/meminfo when available."""
		values: Dict[str, int] = {}

		try:
			with open("/proc/meminfo", "r", encoding="utf-8") as handle:
				for line in handle:
					if ":" not in line:
						continue

					key, value = [part.strip() for part in line.split(":", 1)]
					amount = value.split()[0]
					values[key] = int(amount) * 1024
		except (OSError, ValueError):
			return None

		total_bytes = values.get("MemTotal")
		available_bytes = values.get("MemAvailable", values.get("MemFree"))
		free_bytes = values.get("MemFree")

		if total_bytes is None:
			return None

		snapshot = {"total_bytes": total_bytes}

		if available_bytes is not None:
			snapshot["available_bytes"] = available_bytes

		if free_bytes is not None:
			snapshot["free_bytes"] = free_bytes

		return snapshot

	def _sysconf_memory_snapshot(self) -> Dict[str, int] | None:
		"""Read memory information through sysconf when available."""
		try:
			page_size = os.sysconf("SC_PAGE_SIZE")
			total_pages = os.sysconf("SC_PHYS_PAGES")
			available_pages = os.sysconf("SC_AVPHYS_PAGES")
		except (AttributeError, ValueError, OSError):
			return None

		total_bytes = page_size * total_pages
		available_bytes = page_size * available_pages

		return {
			"total_bytes": total_bytes,
			"available_bytes": available_bytes,
			"free_bytes": available_bytes,
		}

	def _bytes_to_gb(self, value: int | None) -> float | None:
		"""Convert bytes to GiB for human-readable profile data."""
		if value is None:
			return None

		return round(value / (1024 ** 3), 2)