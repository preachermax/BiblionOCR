from __future__ import annotations

from typing import Iterable, List, Protocol

from Core.compute_provider import ComputeProvider


class ProviderBootstrap(Protocol):
	"""Protocol for bootstrap components that discover provider instances."""

	def discover(
		self,
		registered_providers: Iterable[ComputeProvider] = (),
	) -> Iterable[ComputeProvider]:
		"""Return discovered providers that should be registered."""


class ProviderRegistry:
	"""
	In-memory registry for compute provider instances.

	The registry owns provider lifecycle management and optional bootstrap
	discovery. Discovery is delegated to a bootstrap component so provider
	selection and instantiation remain outside the compute engine itself.
	"""

	def __init__(self, bootstrap: ProviderBootstrap | None = None) -> None:
		"""Initialize an empty provider registry."""
		self._providers: List[ComputeProvider] = []
		self._bootstrap = bootstrap
		self._discovered = False

	def set_bootstrap(self, bootstrap: ProviderBootstrap | None) -> None:
		"""Assign or replace the bootstrap used for provider discovery."""
		self._bootstrap = bootstrap
		self._discovered = False

	def register(self, provider: ComputeProvider) -> None:
		"""
		Add a provider instance to the registry.

		Duplicate registrations are ignored so the registry maintains a
		stable set of provider instances.

		Args:
			provider: The provider instance to register.
		"""
		if provider not in self._providers:
			self._providers.append(provider)

	def unregister(self, provider: ComputeProvider) -> None:
		"""
		Remove a provider instance from the registry.

		Missing providers are ignored so callers may safely attempt cleanup
		without coordinating prior registry state.

		Args:
			provider: The provider instance to remove.
		"""
		if provider in self._providers:
			self._providers.remove(provider)

	def providers(self) -> Iterable[ComputeProvider]:
		"""
		Return all registered providers.

		Returns:
			An immutable snapshot of the currently registered providers.
		"""
		return tuple(self._providers)

	def available_providers(self) -> Iterable[ComputeProvider]:
		"""
		Return the subset of registered providers that are usable.

		Returns:
			An immutable snapshot of providers whose ``available()`` method
			currently reports ``True``.
		"""
		return tuple(provider for provider in self._providers if provider.available())

	def discover(self) -> Iterable[ComputeProvider]:
		"""
		Discover providers through the configured bootstrap once.

		Returns:
			An immutable snapshot of the registry after discovery completes.
		"""
		if self._discovered:
			return self.providers()

		if self._bootstrap is not None:
			for provider in self._bootstrap.discover(self.providers()):
				self.register(provider)

		self._discovered = True
		return self.providers()


ComputeRegistry = ProviderRegistry
