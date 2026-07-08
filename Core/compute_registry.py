from __future__ import annotations

from typing import Iterable, List

from Core.compute_provider import ComputeProvider


class ComputeRegistry:
	"""
	In-memory registry for compute provider instances.

	The registry is intentionally limited to provider lifecycle management.
	It does not discover hardware, inspect platforms, or apply scheduling
	logic. Its role is to maintain the collection of provider objects that
	other compute-engine components may query.
	"""

	def __init__(self) -> None:
		"""Initialize an empty provider registry."""
		self._providers: List[ComputeProvider] = []

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
