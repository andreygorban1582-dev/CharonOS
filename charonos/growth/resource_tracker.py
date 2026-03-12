"""Resource tracker and dynamic LLM tier system for CharonOS.

The agent starts at Tier 0 (minimal capabilities) and automatically
upgrades to larger, more capable language models as it gains access
to more resources (API keys, SSH nodes, email accounts).

Tier 0  — No API keys.  Local-only / echo mode.
Tier 1  — 1 API key.  Small models (≤8 B params).
Tier 2  — 2-3 API keys or 1+ SSH nodes.  Mid-size models (≤70 B).
Tier 3  — 4+ API keys and 2+ SSH nodes.  Frontier models.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional

logger = logging.getLogger(__name__)


class Tier(IntEnum):
    """Agent capability tiers."""

    LOCAL = 0
    SMALL = 1
    MEDIUM = 2
    FRONTIER = 3


# Maps each tier to the recommended OpenRouter model identifiers.
# Tier 1 starts with Dolphin Mistral — the uncensored bootstrap model
# the agent grows from.  Higher tiers unlock progressively larger LLMs.
TIER_MODELS: dict[Tier, list[str]] = {
    Tier.LOCAL: [],
    Tier.SMALL: [
        "cognitivecomputations/dolphin-mistral:latest",
        "mistralai/mistral-7b-instruct",
        "meta-llama/llama-3-8b-instruct",
    ],
    Tier.MEDIUM: [
        "deepseek/deepseek-chat",
        "cognitivecomputations/dolphin-mixtral:latest",
        "meta-llama/llama-3-70b-instruct",
    ],
    Tier.FRONTIER: [
        "deepseek/deepseek-chat",
        "anthropic/claude-sonnet-4",
        "openai/gpt-4o",
        "meta-llama/llama-3.1-405b-instruct",
    ],
}

# The bootstrap model the agent starts with at Tier 1
BOOTSTRAP_MODEL = "cognitivecomputations/dolphin-mistral:latest"

# Context window sizes (tokens) per tier
TIER_CONTEXT_SIZES: dict[Tier, int] = {
    Tier.LOCAL: 2_000,
    Tier.SMALL: 8_000,
    Tier.MEDIUM: 32_000,
    Tier.FRONTIER: 128_000,
}


@dataclass
class ResourceInventory:
    """Tracks every resource the agent currently has access to."""

    api_keys: list[str] = field(default_factory=list)
    ssh_hosts: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Mutation helpers (used by growth module)
    # ------------------------------------------------------------------

    def add_api_key(self, key: str) -> None:
        if key and key not in self.api_keys:
            self.api_keys.append(key)
            logger.info("Resource added: API key (total: %d)", len(self.api_keys))

    def add_ssh_host(self, host: str) -> None:
        if host and host not in self.ssh_hosts:
            self.ssh_hosts.append(host)
            logger.info("Resource added: SSH host %s (total: %d)", host, len(self.ssh_hosts))

    def add_email(self, email: str) -> None:
        if email and email not in self.emails:
            self.emails.append(email)
            logger.info("Resource added: email (total: %d)", len(self.emails))

    # ------------------------------------------------------------------
    # Tier calculation
    # ------------------------------------------------------------------

    def compute_tier(self) -> Tier:
        """Determine the current tier based on available resources."""
        n_keys = len(self.api_keys)
        n_hosts = len(self.ssh_hosts)

        if n_keys == 0:
            return Tier.LOCAL
        if n_keys >= 4 and n_hosts >= 2:
            return Tier.FRONTIER
        if n_keys >= 2 or n_hosts >= 1:
            return Tier.MEDIUM
        return Tier.SMALL

    def get_recommended_model(self) -> Optional[str]:
        """Return the best model available at the current tier."""
        tier = self.compute_tier()
        models = TIER_MODELS.get(tier, [])
        return models[0] if models else None

    def get_context_budget(self) -> int:
        """Return the token budget for the current tier."""
        return TIER_CONTEXT_SIZES[self.compute_tier()]


def build_inventory_from_config(config: "CharonConfig") -> ResourceInventory:
    """Populate a ResourceInventory from a CharonConfig."""
    inv = ResourceInventory()

    if config.openrouter.api_key:
        inv.add_api_key(config.openrouter.api_key)
    if config.deepseek.api_key:
        inv.add_api_key(config.deepseek.api_key)
    for k in config.extra_api_keys:
        inv.add_api_key(k)

    if config.deepseek.email:
        inv.add_email(config.deepseek.email)
    for e in config.extra_emails:
        inv.add_email(e)

    return inv
