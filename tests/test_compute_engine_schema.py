from __future__ import annotations

import unittest

from Core.compute_engine import ComputeEngine
from Core.compute_registry import ProviderRegistry
from Developer.hardware.providers.bootstrap import ProviderBootstrap
from Developer.hardware.providers.cpu import CPUProvider
from Developer.hardware.providers.memory import MemoryProvider
from Developer.hardware.providers.storage import StorageProvider


class ComputeEngineSchemaTests(unittest.TestCase):
	def _engine(self) -> ComputeEngine:
		bootstrap = ProviderBootstrap((CPUProvider, MemoryProvider, StorageProvider))
		return ComputeEngine(registry=ProviderRegistry(bootstrap))

	def test_profile_groups_cpu_memory_and_storage_sections(self) -> None:
		profile = self._engine().get_profile()

		self.assertIn("cpu", profile)
		self.assertIn("memory", profile)
		self.assertIn("storage", profile)
		self.assertIn("providers", profile)
		self.assertIn("available_providers", profile)
		self.assertIn("logical_threads", profile["cpu"])
		self.assertIn("threads", profile["cpu"])
		self.assertIn("cores", profile["cpu"])
		self.assertIn("total_bytes", profile["memory"])
		self.assertIn("installed_gb", profile["memory"])
		self.assertIn("path", profile["storage"])
		self.assertIn("capacity_gb", profile["storage"])

	def test_status_groups_cpu_memory_and_storage_sections(self) -> None:
		status = self._engine().get_status()

		self.assertIn("cpu", status)
		self.assertIn("memory", status)
		self.assertIn("storage", status)
		self.assertIn("providers", status)
		self.assertIn("logical_threads", status["cpu"])
		self.assertIn("threads", status["cpu"])
		self.assertIn("used_bytes", status["memory"])
		self.assertIn("installed_bytes", status["memory"])
		self.assertIn("free_bytes", status["storage"])
		self.assertIn("capacity_bytes", status["storage"])

	def test_missing_future_provider_sections_do_not_break_output(self) -> None:
		engine = self._engine()
		profile = engine.get_profile()
		status = engine.get_status()

		self.assertEqual([], profile["gpus"])
		self.assertEqual([], status["gpus"])
		self.assertFalse(profile["cuda"]["available"])
		self.assertFalse(status["cuda"]["available"])
		self.assertEqual(0, profile["cuda"]["device_count"])
		self.assertIsNone(profile["cuda"]["driver_version"])

	def test_empty_registry_still_returns_stable_schema(self) -> None:
		engine = ComputeEngine(registry=ProviderRegistry(ProviderBootstrap(())))
		profile = engine.get_profile()
		status = engine.get_status()

		self.assertEqual([], profile["available_providers"])
		self.assertEqual([], profile["providers"])
		self.assertIsNone(profile["cpu"]["model"])
		self.assertIsNone(profile["memory"]["installed_gb"])
		self.assertIsNone(profile["storage"]["capacity_gb"])
		self.assertEqual([], status["providers"])
		self.assertIsNone(status["cpu"]["threads"])
		self.assertIsNone(status["memory"]["used_bytes"])
		self.assertIsNone(status["storage"]["free_bytes"])


if __name__ == "__main__":
	unittest.main()