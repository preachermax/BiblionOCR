from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping

from Core.compute_provider import ComputeProvider
from Core.compute_registry import ProviderRegistry
from Developer.hardware.providers.bootstrap import default_provider_bootstrap


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

    def __init__(
        self,
        registry: ProviderRegistry | None = None,
        auto_discover: bool = True,
    ) -> None:
        """
        Initialize the compute engine.

        Args:
            registry: Optional provider registry. When omitted, the engine
                creates a new registry configured with the default provider
                bootstrap.
            auto_discover: When ``True``, the engine lazily bootstraps
                providers before provider queries and profile/status access.
        """
        self._registry = registry or ProviderRegistry(default_provider_bootstrap())
        self._auto_discover = auto_discover

    def register_provider(self, provider: ComputeProvider) -> None:
        """Register a provider with the engine's registry."""
        self._registry.register(provider)

    def unregister_provider(self, provider: ComputeProvider) -> None:
        """Remove a provider from the engine's registry."""
        self._registry.unregister(provider)

    def providers(self) -> Iterable[ComputeProvider]:
        """Return all providers currently registered with the engine."""
        self._bootstrap_if_enabled()
        return self._registry.providers()

    def available_providers(self) -> Iterable[ComputeProvider]:
        """Return only providers whose availability currently resolves true."""
        self._bootstrap_if_enabled()
        return self._registry.available_providers()

    def bootstrap_providers(self) -> Iterable[ComputeProvider]:
        """Discover and register providers through the configured registry."""
        return self._registry.discover()

    def get_profile(self) -> Mapping[str, Any]:
        """
        Return a normalized compute profile for registered providers.

        The public profile groups hardware information into stable top-level
        sections such as ``cpu``, ``memory``, ``storage``, ``gpus``, and
        ``cuda``. Raw provider output is preserved alongside the normalized
        view for callers that need provider-specific detail.
        """
        self._bootstrap_if_enabled()
        provider_profiles = [self._provider_profile(provider) for provider in self.providers()]
        profile = self._empty_profile_schema()
        profile.update(self._normalized_profile_sections(provider_profiles))
        profile["providers"] = provider_profiles
        profile["available_providers"] = [
            self._provider_name(provider) for provider in self.available_providers()
        ]
        return profile

    def get_status(self) -> Mapping[str, Any]:
        """
        Return normalized runtime status for registered providers.

        The public status groups runtime information into the same stable
        top-level sections as the profile output. Raw provider status is
        preserved separately for provider-specific consumers.
        """
        self._bootstrap_if_enabled()
        provider_status = [self._provider_status(provider) for provider in self.providers()]
        status = self._empty_status_schema()
        status.update(self._normalized_status_sections(provider_status))
        status["providers"] = provider_status
        return status

    def _bootstrap_if_enabled(self) -> None:
        """Run lazy provider discovery when the engine is configured to do so."""
        if self._auto_discover:
            self._registry.discover()

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

    def _empty_profile_schema(self) -> Dict[str, Any]:
        """Return the default normalized compute-engine profile schema."""
        return {
            "cpu": {
                "vendor": None,
                "model": None,
                "architecture": None,
                "platform": None,
                "cores": None,
                "threads": None,
                "logical_threads": None,
            },
            "memory": {
                "installed_bytes": None,
                "installed_gb": None,
                "total_bytes": None,
                "total_gb": None,
                "available_bytes": None,
            },
            "storage": {
                "path": None,
                "capacity_bytes": None,
                "capacity_gb": None,
                "total_bytes": None,
                "total_gb": None,
                "available_bytes": None,
                "free_bytes": None,
            },
            "gpus": [],
            "cuda": {
                "available": False,
                "version": None,
                "device_count": 0,
                "devices": [],
                "driver_version": None,
            },
            "providers": [],
            "available_providers": [],
        }

    def _empty_status_schema(self) -> Dict[str, Any]:
        """Return the default normalized compute-engine status schema."""
        return {
            "cpu": {
                "threads": None,
                "logical_threads": None,
                "load_average_1m": None,
                "load_average_5m": None,
                "load_average_15m": None,
            },
            "memory": {
                "installed_bytes": None,
                "total_bytes": None,
                "available_bytes": None,
                "free_bytes": None,
                "used_bytes": None,
            },
            "storage": {
                "path": None,
                "capacity_bytes": None,
                "total_bytes": None,
                "available_bytes": None,
                "free_bytes": None,
                "used_bytes": None,
            },
            "gpus": [],
            "cuda": {
                "available": False,
                "version": None,
                "device_count": 0,
                "devices": [],
                "driver_version": None,
            },
            "providers": [],
        }

    def _normalized_profile_sections(
        self,
        provider_profiles: Iterable[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        """Build normalized top-level profile sections from raw provider data."""
        return self._normalized_sections(provider_profiles, payload_key="profile")

    def _normalized_status_sections(
        self,
        provider_status: Iterable[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        """Build normalized top-level status sections from raw provider data."""
        return self._normalized_sections(provider_status, payload_key="status")

    def _normalized_sections(
        self,
        provider_entries: Iterable[Mapping[str, Any]],
        payload_key: str,
    ) -> Dict[str, Any]:
        """Map raw provider entries into the public compute-engine schema."""
        normalized = (
            self._empty_profile_schema()
            if payload_key == "profile"
            else self._empty_status_schema()
        )

        for entry in provider_entries:
            payload = dict(entry.get(payload_key, {}))
            resource = payload.pop("resource", None)

            if resource == "cpu":
                normalized["cpu"] = self._normalize_cpu_section(payload_key, payload, normalized["cpu"])
            elif resource == "memory":
                normalized["memory"] = self._normalize_memory_section(
                    payload_key,
                    payload,
                    normalized["memory"],
                )
            elif resource == "storage":
                normalized["storage"] = self._normalize_storage_section(
                    payload_key,
                    payload,
                    normalized["storage"],
                )
            elif resource == "gpu":
                normalized["gpus"] = list(payload.get("devices", []))
            elif resource == "cuda":
                cuda_section = dict(normalized["cuda"])
                cuda_section.update(payload)
                normalized["cuda"] = cuda_section

        return normalized

    def _normalize_cpu_section(
        self,
        payload_key: str,
        payload: Mapping[str, Any],
        default_section: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Normalize CPU data into a stable public section."""
        section = dict(default_section)
        section.update(payload)

        threads = payload.get("threads", payload.get("logical_threads"))
        section["threads"] = threads
        section["logical_threads"] = payload.get("logical_threads", threads)

        if payload_key == "profile":
            section["cores"] = payload.get("cores")

        return section

    def _normalize_memory_section(
        self,
        payload_key: str,
        payload: Mapping[str, Any],
        default_section: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Normalize memory data into a stable public section."""
        section = dict(default_section)
        section.update(payload)

        installed_bytes = payload.get("installed_bytes", payload.get("total_bytes"))
        section["installed_bytes"] = installed_bytes
        section["total_bytes"] = payload.get("total_bytes", installed_bytes)

        if payload_key == "profile":
            installed_gb = payload.get("installed_gb", payload.get("total_gb"))
            section["installed_gb"] = installed_gb
            section["total_gb"] = payload.get("total_gb", installed_gb)

        return section

    def _normalize_storage_section(
        self,
        payload_key: str,
        payload: Mapping[str, Any],
        default_section: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Normalize storage data into a stable public section."""
        section = dict(default_section)
        section.update(payload)

        capacity_bytes = payload.get("capacity_bytes", payload.get("total_bytes"))
        section["capacity_bytes"] = capacity_bytes
        section["total_bytes"] = payload.get("total_bytes", capacity_bytes)

        available_bytes = payload.get("available_bytes", payload.get("free_bytes"))
        section["available_bytes"] = available_bytes
        section["free_bytes"] = payload.get("free_bytes", available_bytes)

        if payload_key == "profile":
            capacity_gb = payload.get("capacity_gb", payload.get("total_gb"))
            section["capacity_gb"] = capacity_gb
            section["total_gb"] = payload.get("total_gb", capacity_gb)

        return section