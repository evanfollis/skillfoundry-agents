#!/usr/bin/env python3
"""Profile loading and resolution for Skillfoundry agent roles."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


PROFILE_SECTIONS = {
    "persona": {"summary"},
    "frontdoor": {"mission", "focus", "deliverables"},
    "policy": {"promotion_validation_kinds", "preferred_bundle_ids"},
    "handoff": {"expected_outputs", "downstream_profiles"},
}


class ProfileError(Exception):
    """Raised when a role profile or profile resolution is invalid."""


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise ProfileError(message)


def load_toml(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as exc:
        raise ProfileError(f"{path}: invalid TOML: {exc}") from exc


def validate_string_list(value: Any, *, field_name: str) -> list[str]:
    ensure(isinstance(value, list), f"{field_name}: expected array")
    normalized: list[str] = []
    for index, item in enumerate(value):
        ensure(isinstance(item, str) and item.strip(), f"{field_name}[{index}]: expected non-empty string")
        normalized.append(item.strip())
    ensure(len(set(normalized)) == len(normalized), f"{field_name}: values must be distinct")
    return normalized


def validate_profile_manifest(profile_dir: Path) -> dict[str, Any]:
    manifest = profile_dir / "profile.toml"
    ensure(manifest.exists(), f"{profile_dir}: missing profile.toml")
    config = load_toml(manifest)
    allowed_top_level = {"schema_version", "profile_id", "name", "extends", *PROFILE_SECTIONS}
    ensure(set(config).issubset(allowed_top_level), f"{manifest}: unexpected top-level keys")
    ensure(config.get("schema_version") == "1", f"{manifest}: schema_version must be '1'")
    ensure(config.get("profile_id") == profile_dir.name, f"{manifest}: profile_id must match directory name")
    ensure(isinstance(config.get("name"), str) and config["name"].strip(), f"{manifest}: name is required")
    extends = config.get("extends", [])
    ensure(isinstance(extends, list), f"{manifest}: extends must be an array when present")
    validate_string_list(extends, field_name=f"{manifest}: extends")
    for section_name, allowed_keys in PROFILE_SECTIONS.items():
        section = config.get(section_name, {})
        ensure(isinstance(section, dict), f"{manifest}: [{section_name}] must be a table when present")
        ensure(set(section).issubset(allowed_keys), f"{manifest}: unexpected keys in [{section_name}]")
        for key, value in section.items():
            if key == "summary":
                ensure(isinstance(value, str) and value.strip(), f"{manifest}: {section_name}.{key} must be a non-empty string")
            else:
                validate_string_list(value, field_name=f"{manifest}: {section_name}.{key}")
    return config


def load_profiles(repo_root: Path) -> dict[str, dict[str, Any]]:
    profiles_dir = repo_root / "profiles"
    ensure(profiles_dir.exists(), f"{profiles_dir}: missing profiles directory")
    ensure(profiles_dir.is_dir(), f"{profiles_dir}: expected directory")
    profiles = {
        profile_dir.name: validate_profile_manifest(profile_dir)
        for profile_dir in sorted(path for path in profiles_dir.iterdir() if path.is_dir() and not path.name.startswith("."))
    }
    ensure(profiles, f"{profiles_dir}: at least one profile is required")
    for profile_id, config in profiles.items():
        for parent in config.get("extends", []):
            ensure(parent in profiles, f"{profiles_dir / profile_id / 'profile.toml'}: extends unknown profile {parent!r}")
    for profile_id in profiles:
        resolve_profile(profile_id, profiles)
    return profiles


def resolve_profile(profile_id: str, profiles: dict[str, dict[str, Any]], cache: dict[str, dict[str, Any]] | None = None, stack: tuple[str, ...] = ()) -> dict[str, Any]:
    if cache is None:
        cache = {}
    if profile_id in cache:
        return cache[profile_id]
    ensure(profile_id in profiles, f"unknown profile: {profile_id}")
    ensure(profile_id not in stack, f"profile inheritance cycle detected: {' -> '.join((*stack, profile_id))}")
    config = profiles[profile_id]
    resolved = {
        "profile_id": profile_id,
        "name": config["name"].strip(),
        "profile_stack": [],
        "persona": {},
        "frontdoor": {"mission": [], "focus": [], "deliverables": []},
        "policy": {"promotion_validation_kinds": [], "preferred_bundle_ids": []},
        "handoff": {"expected_outputs": [], "downstream_profiles": []},
    }
    for parent in config.get("extends", []):
        resolved = _merge_profile(resolved, resolve_profile(parent, profiles, cache, (*stack, profile_id)))
    resolved = _merge_profile(resolved, config)
    cache[profile_id] = resolved
    return resolved


def resolve_profile_stack(profile_ids: list[str], profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    ensure(profile_ids, "runtime.profiles must contain at least one profile")
    merged = {
        "profile_stack": [],
        "persona": {},
        "frontdoor": {"mission": [], "focus": [], "deliverables": []},
        "policy": {"promotion_validation_kinds": [], "preferred_bundle_ids": []},
        "handoff": {"expected_outputs": [], "downstream_profiles": []},
    }
    cache: dict[str, dict[str, Any]] = {}
    for profile_id in profile_ids:
        merged = _merge_profile(merged, resolve_profile(profile_id, profiles, cache))
    return merged


def _merge_profile(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "profile_stack": list(base.get("profile_stack", [])),
        "persona": dict(base.get("persona", {})),
        "frontdoor": {key: list(value) for key, value in base.get("frontdoor", {}).items()},
        "policy": {key: list(value) for key, value in base.get("policy", {}).items()},
        "handoff": {key: list(value) for key, value in base.get("handoff", {}).items()},
    }
    for inherited_profile_id in overlay.get("profile_stack", []):
        if inherited_profile_id not in merged["profile_stack"]:
            merged["profile_stack"].append(inherited_profile_id)
    profile_id = overlay.get("profile_id")
    if isinstance(profile_id, str) and profile_id not in merged["profile_stack"]:
        merged["profile_stack"].append(profile_id)
    if "name" in overlay:
        merged["name"] = overlay["name"]
    persona = overlay.get("persona", {})
    if "summary" in persona:
        merged["persona"]["summary"] = persona["summary"].strip()
    for section_name in ("frontdoor", "policy", "handoff"):
        for key, values in overlay.get(section_name, {}).items():
            for value in values:
                if value not in merged[section_name][key]:
                    merged[section_name][key].append(value)
    return merged
