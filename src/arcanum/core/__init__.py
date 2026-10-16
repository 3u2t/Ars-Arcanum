"""Core DAL, caching, security sandbox, hardened parsers, and typed constitution primitives."""

from __future__ import annotations

from scripts.lib.audit_hardening import (
    HardenedArchiveLimits,
    normalize_cjk_and_unicode_prose,
    parse_frontmatter_hardened,
    parse_xml_safe_bytes,
    sanitize_critic_markup,
    validate_safe_zip_archive,
)
from scripts.lib.plugin_sandbox import SandboxedPluginResult, run_plugin_sandboxed
from scripts.lib.typed_constitution import (
    AuthorialConstitution,
    CraftPolicyThresholds,
    resolve_constitution_cascade,
)
from scripts.lib.vault_index import (
    ProseMetrics,
    VaultDocumentNode,
    VaultIndex,
    atomic_write,
    is_safe_subpath,
    parse_frontmatter,
)

__all__ = [
    "AuthorialConstitution",
    "CraftPolicyThresholds",
    "HardenedArchiveLimits",
    "ProseMetrics",
    "SandboxedPluginResult",
    "VaultDocumentNode",
    "VaultIndex",
    "atomic_write",
    "is_safe_subpath",
    "normalize_cjk_and_unicode_prose",
    "parse_frontmatter",
    "parse_frontmatter_hardened",
    "parse_xml_safe_bytes",
    "resolve_constitution_cascade",
    "run_plugin_sandboxed",
    "sanitize_critic_markup",
    "validate_safe_zip_archive",
]
