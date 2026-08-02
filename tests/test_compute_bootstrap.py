from __future__ import annotations

import unittest
from typing import Any, Iterable, Mapping

from Core.compute_engine import ComputeEngine
from Core.compute_provider import ComputeProvider
from Core.compute_registry import ProviderRegistry
from Developer.hardware.providers.bootstrap import ProviderBootstrap
from Developer.hardware.providers.cuda import CUDAProvider
from Developer.hardware.providers.gpu import GPUProvider


class FakeAvailableProvider(ComputeProvider):
	def available(self) -> bool:
		return True

	def profile(self) -> Mapping[str, Any]:
		return {"resource": "fake-available"}

	def status(self) -> Mapping[str, Any]:
		return {"healthy": True}


class FakeUnavailableProvider(ComputeProvider):
	def available(self) -> bool:
		return False

	def profile(self) -> Mapping[str, Any]:
		return {"resource": "fake-unavailable"}

	def status(self) -> Mapping[str, Any]:
		return {"healthy": False}


class RecordingBootstrap(ProviderBootstrap):
	def __init__(self, providers: Iterable[type[ComputeProvider]]) -> None:
		super().__init__(providers)
		self.calls = 0

	def discover(
		self,
		registered_providers: Iterable[ComputeProvider] = (),
	) -> Iterable[ComputeProvider]:
		self.calls += 1
		return super().discover(registered_providers)


class ProviderBootstrapTests(unittest.TestCase):
	def test_registry_discovery_registers_only_available_providers(self) -> None:
		bootstrap = ProviderBootstrap((FakeAvailableProvider, FakeUnavailableProvider))
		registry = ProviderRegistry(bootstrap)

		providers = tuple(registry.discover())

		self.assertEqual(1, len(providers))
		self.assertIsInstance(providers[0], FakeAvailableProvider)
		self.assertEqual(providers, tuple(registry.available_providers()))

	def test_engine_lazy_bootstrap_preserves_manual_provider_registration(self) -> None:
		manual_provider = FakeAvailableProvider()
		bootstrap = RecordingBootstrap((FakeAvailableProvider,))
		registry = ProviderRegistry(bootstrap)
		registry.register(manual_provider)
		engine = ComputeEngine(registry=registry)

		providers = tuple(engine.providers())

		self.assertEqual(1, bootstrap.calls)
		self.assertEqual(1, len(providers))
		self.assertIs(providers[0], manual_provider)

	def test_engine_bootstrap_runs_once_across_multiple_queries(self) -> None:
		bootstrap = RecordingBootstrap((FakeAvailableProvider,))
		engine = ComputeEngine(registry=ProviderRegistry(bootstrap))

		engine.providers()
		engine.get_profile()
		engine.get_status()

		self.assertEqual(1, bootstrap.calls)

	def test_default_factories_include_gpu_and_cuda_providers(self) -> None:
		factories = ProviderBootstrap.default_factories()

		self.assertIn(GPUProvider, factories)
		self.assertIn(CUDAProvider, factories)


if __name__ == "__main__":
	unittest.main()