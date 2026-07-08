from __future__ import annotations

import shutil
from typing import Any, Mapping

from Core.compute_provider import ComputeProvider


class StorageProvider(ComputeProvider):
	"""Provide storage capacity and runtime usage information."""

	def __init__(self, path: str = "/") -> None:
		"""Initialize the provider for a specific filesystem path."""
		self._path = path

	def available(self) -> bool:
		"""Return whether storage usage can be read for the configured path."""
		return self._disk_usage() is not None

	def profile(self) -> Mapping[str, Any]:
		"""Return descriptive storage capacity metadata for the path."""
		usage = self._disk_usage()

		return {
			"resource": "storage",
			"path": self._path,
			"total_bytes": None if usage is None else usage.total,
			"total_gb": None if usage is None else round(usage.total / (1024 ** 3), 2),
		}

	def status(self) -> Mapping[str, Any]:
		"""Return current usage details for the configured storage path."""
		usage = self._disk_usage()

		return {
			"resource": "storage",
			"path": self._path,
			"total_bytes": None if usage is None else usage.total,
			"used_bytes": None if usage is None else usage.used,
			"free_bytes": None if usage is None else usage.free,
		}

	def _disk_usage(self) -> shutil._ntuple_diskusage | None:
		"""Return the disk usage tuple for the configured path."""
		try:
			return shutil.disk_usage(self._path)
		except OSError:
			return None