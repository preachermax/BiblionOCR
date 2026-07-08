from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping

from Core.compute_provider import ComputeProvider
from Core.compute_registry import ComputeRegistry


class ComputeEngine:
    """
    Central manager for compute provider coordination.

    The compute engine exposes the public API through which application
    code interacts with registered compute providers. It owns a provider
    registry, aggregates provider information, and presents a unified view
    of provider profile and status data.

    This class intentionally does not perform hardware discovery or embed
    provider-specific knowledge. All platform details remain inside
    concrete provider implementations.
    """

    def __init__(self, registry: ComputeRegistry | None = None) -> None:
        """
        Initialize the compute engine.

        Args:
            registry: Optional provider registry. When omitted, the engine
                creates a new empty registry for its own use.
        """
        self._registry = registry or ComputeRegistry()

    def register_provider(self, provider: ComputeProvider) -> None:
        """Register a provider with the engine's registry."""
        self._registry.register(provider)

    def unregister_provider(self, provider: ComputeProvider) -> None:
        """Remove a provider from the engine's registry."""
        self._registry.unregister(provider)

    def providers(self) -> Iterable[ComputeProvider]:
        """Return all providers currently registered with the engine."""
        return self._registry.providers()

    def available_providers(self) -> Iterable[ComputeProvider]:
        """Return only providers whose availability currently resolves true."""
        return self._registry.available_providers()

    def get_profile(self) -> Mapping[str, Any]:
        """
        Return a unified profile view for registered providers.

        The result is intentionally generic so the compute engine can compose
        information from current and future provider types without hard-coding
        knowledge about specific accelerator technologies.
        """
        return {
            "providers": [self._provider_profile(provider) for provider in self.providers()],
            "available_providers": [
                self._provider_name(provider) for provider in self.available_providers()
            ],
        }

    def get_status(self) -> Mapping[str, Any]:
        """
        Return current runtime status for registered providers.

        Status entries are grouped per provider so callers can inspect the
        current runtime view without requiring direct access to provider
        implementations.
        """
        return {
            "providers": [self._provider_status(provider) for provider in self.providers()],
        }

    def _provider_name(self, provider: ComputeProvider) -> str:
        """Return a stable engine-facing name for a provider instance."""
        return provider.__class__.__name__

    def _provider_profile(self, provider: ComputeProvider) -> Dict[str, Any]:
        """Compose profile metadata for a single registered provider."""
        return {
            "provider": self._provider_name(provider),
            "available": provider.available(),
            "profile": dict(provider.profile()),
        }

    def _provider_status(self, provider: ComputeProvider) -> Dict[str, Any]:
        """Compose runtime status metadata for a single registered provider."""
        return {
            "provider": self._provider_name(provider),
            "available": provider.available(),
            "status": dict(provider.status()),
        }