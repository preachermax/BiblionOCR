from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class ComputeProvider(ABC):
	"""
	Abstract contract for all compute resource providers.

	Providers encapsulate the details required to represent a single
	computational capability source. The compute engine interacts with
	providers only through this interface, allowing future provider types
	to evolve independently from the engine and registry layers.

	This base class intentionally contains no platform logic, no discovery
	behavior, and no assumptions about specific hardware vendors or APIs.
	"""

	@abstractmethod
	def available(self) -> bool:
		"""
		Report whether this provider is currently usable.

		Implementations should answer only for the provider instance they
		represent. Returning ``True`` indicates that the provider can supply
		profile and status information to the compute engine. Returning
		``False`` indicates that the provider is presently unavailable.

		Returns:
			``True`` when the provider is usable, otherwise ``False``.
		"""

	@abstractmethod
	def profile(self) -> Mapping[str, Any]:
		"""
		Return a stable descriptive profile for this provider.

		The profile should contain structured metadata that identifies the
		capabilities exposed by the provider. Implementations should prefer
		predictable keys and serializable values so the profile can be
		composed into broader compute-engine responses.

		Returns:
			A mapping describing the provider's capabilities and identity.
		"""

	@abstractmethod
	def status(self) -> Mapping[str, Any]:
		"""
		Return current runtime status for this provider.

		Status data is intended for operational visibility and may change
		over time as workloads run. Implementations should return structured,
		serializable values suitable for monitoring, dashboards, or engine
		level summaries.

		Returns:
			A mapping describing the provider's current runtime state.
		"""
