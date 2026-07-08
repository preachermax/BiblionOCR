from __future__ import annotations

from typing import Callable, Iterable, Tuple

from Core.compute_provider import ComputeProvider
from Developer.hardware.providers.cpu import CPUProvider
from Developer.hardware.providers.cuda import CUDAProvider
from Developer.hardware.providers.gpu import GPUProvider
from Developer.hardware.providers.memory import MemoryProvider
from Developer.hardware.providers.storage import StorageProvider

ProviderFactory = Callable[[], ComputeProvider]


class ProviderBootstrap:
	"""
	Default provider bootstrap for the compute engine.

	The bootstrap owns knowledge of which provider implementations should be
	considered during automatic discovery. This keeps the compute engine free
	of provider-specific imports while allowing future accelerator providers to
	be added in one place.
	"""

	def __init__(self, factories: Iterable[ProviderFactory] | None = None) -> None:
		"""Initialize the bootstrap with provider factories."""
		self._factories = tuple(self.default_factories() if factories is None else factories)

	def discover(
		self,
		registered_providers: Iterable[ComputeProvider] = (),
	) -> Iterable[ComputeProvider]:
		"""Instantiate and return available providers not already registered."""
		existing_types = {provider.__class__ for provider in registered_providers}
		discovered = []

		for factory in self._factories:
			provider = self._build_provider(factory)
			if provider is None:
				continue

			if provider.__class__ in existing_types:
				continue

			if provider.available():
				discovered.append(provider)
				existing_types.add(provider.__class__)

		return tuple(discovered)

	@staticmethod
	def default_factories() -> Tuple[ProviderFactory, ...]:
		"""Return the default provider factories for the current phase."""
		return (
			CPUProvider,
			MemoryProvider,
			StorageProvider,
			GPUProvider,
			CUDAProvider,
		)

	def _build_provider(self, factory: ProviderFactory) -> ComputeProvider | None:
		"""Instantiate a provider while isolating bootstrap failures."""
		try:
			return factory()
		except Exception:
			return None


def default_provider_bootstrap() -> ProviderBootstrap:
	"""Return the default provider bootstrap instance for the current phase."""
	return ProviderBootstrap()