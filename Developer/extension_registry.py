from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path


MANIFEST_FILENAME = "extension.json"
IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def validate_identifier(value: str, label: str) -> str:
    value = str(value or "").strip()
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"Invalid {label}: {value!r}")
    return value


@dataclass(frozen=True)
class ServiceManifest:
    service_id: str
    name: str
    description: str
    entry_point: str


@dataclass(frozen=True)
class ExtensionManifest:
    extension_id: str
    name: str
    version: str
    description: str
    services: tuple[ServiceManifest, ...]
    root: Path


def default_extension_root() -> Path:
    override = os.environ.get("BIBLIONOCR_EXTENSION_HOME")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "BiblionOCR" / "extensions"


def load_manifest(root: Path) -> ExtensionManifest:
    root = Path(root).resolve()
    payload = json.loads((root / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError(f"Unsupported extension manifest schema: {payload.get('schema_version')}")

    extension_id = validate_identifier(payload.get("id"), "extension id")
    name = str(payload.get("name") or "").strip()
    version = str(payload.get("version") or "").strip()
    if not extension_id or not name or not version:
        raise ValueError("Extension manifests require id, name, and version")

    services = tuple(
        ServiceManifest(
            service_id=validate_identifier(service["id"], "service id"),
            name=str(service["name"]),
            description=str(service.get("description") or ""),
            entry_point=str(service["entry_point"]),
        )
        for service in payload.get("services", ())
    )
    if len({service.service_id for service in services}) != len(services):
        raise ValueError(f"Duplicate service id in extension {extension_id}")
    return ExtensionManifest(
        extension_id=extension_id,
        name=name,
        version=version,
        description=str(payload.get("description") or ""),
        services=services,
        root=root,
    )


class ExtensionRegistry:
    def __init__(self, bundled_root=None, install_root=None):
        self.bundled_root = Path(
            bundled_root or Path(__file__).resolve().parent / "extensions"
        ).resolve()
        self.install_root = Path(install_root or default_extension_root()).resolve()

    def bundled_extensions(self) -> tuple[ExtensionManifest, ...]:
        if not self.bundled_root.is_dir():
            return ()
        manifests = []
        for candidate in sorted(self.bundled_root.iterdir()):
            if candidate.is_dir() and (candidate / MANIFEST_FILENAME).is_file():
                manifests.append(load_manifest(candidate))
        return tuple(manifests)

    def installed_extensions(self) -> tuple[ExtensionManifest, ...]:
        if not self.install_root.is_dir():
            return ()
        manifests = []
        for candidate in sorted(self.install_root.iterdir()):
            if candidate.is_dir() and (candidate / MANIFEST_FILENAME).is_file():
                manifests.append(load_manifest(candidate))
        return tuple(manifests)

    def bundled_extension(self, extension_id: str) -> ExtensionManifest:
        for manifest in self.bundled_extensions():
            if manifest.extension_id == extension_id:
                return manifest
        raise KeyError(f"Unknown bundled extension: {extension_id}")

    def installed_extension(self, extension_id: str) -> ExtensionManifest:
        for manifest in self.installed_extensions():
            if manifest.extension_id == extension_id:
                return manifest
        raise KeyError(f"Extension is not installed: {extension_id}")

    def is_installed(self, extension_id: str) -> bool:
        try:
            self.installed_extension(extension_id)
        except KeyError:
            return False
        return True

    def install(self, extension_id: str) -> ExtensionManifest:
        source = self.bundled_extension(extension_id)
        destination = self.install_root / source.extension_id
        self.install_root.mkdir(parents=True, exist_ok=True)
        staging = self.install_root / f".{source.extension_id}.installing"
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(source.root, staging, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        if destination.exists():
            shutil.rmtree(destination)
        staging.replace(destination)
        return load_manifest(destination)

    def uninstall(self, extension_id: str) -> None:
        extension_id = validate_identifier(extension_id, "extension id")
        destination = self.install_root / extension_id
        if destination.is_dir():
            shutil.rmtree(destination)

    def load_service(self, extension_id: str, service_id: str):
        extension_id = validate_identifier(extension_id, "extension id")
        service_id = validate_identifier(service_id, "service id")
        extension = self.installed_extension(extension_id)
        service = next(
            (candidate for candidate in extension.services if candidate.service_id == service_id),
            None,
        )
        if service is None:
            raise KeyError(f"Unknown service {service_id} in extension {extension_id}")

        module_path_text, separator, symbol_name = service.entry_point.partition(":")
        if not separator or not symbol_name:
            raise ValueError(f"Invalid service entry point: {service.entry_point}")
        module_path = (extension.root / module_path_text).resolve()
        if extension.root not in module_path.parents or not module_path.is_file():
            raise ValueError(f"Service entry point escapes extension root: {service.entry_point}")

        module_name = f"biblion_extension_{extension_id.replace('-', '_')}_{service_id.replace('-', '_')}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load extension service module: {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        try:
            return getattr(module, symbol_name)
        except AttributeError as exc:
            raise ImportError(f"Service symbol not found: {service.entry_point}") from exc