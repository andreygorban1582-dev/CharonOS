"""Self-improvement module for CharonOS.

Monitors the agent's resource inventory and triggers upgrades:
  - Adjusts LLM model selection when new API keys arrive.
  - Expands the rolling context window when compute grows.
  - Logs growth events for the agent's own learning loop.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from charonos.growth.resource_tracker import (
    ResourceInventory,
    Tier,
    TIER_CONTEXT_SIZES,
    TIER_MODELS,
)

logger = logging.getLogger(__name__)


@dataclass
class GrowthEvent:
    """Record of a single growth event."""

    timestamp: float
    old_tier: Tier
    new_tier: Tier
    description: str


class GrowthEngine:
    """Watches the resource inventory and orchestrates upgrades."""

    def __init__(self, inventory: ResourceInventory) -> None:
        self.inventory = inventory
        self._current_tier: Tier = inventory.compute_tier()
        self._history: list[GrowthEvent] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def current_tier(self) -> Tier:
        return self._current_tier

    @property
    def history(self) -> list[GrowthEvent]:
        return list(self._history)

    def check_for_upgrade(self) -> GrowthEvent | None:
        """Re-evaluate the tier and record an upgrade if it changed."""
        new_tier = self.inventory.compute_tier()
        if new_tier == self._current_tier:
            return None

        event = GrowthEvent(
            timestamp=time.time(),
            old_tier=self._current_tier,
            new_tier=new_tier,
            description=self._describe_upgrade(self._current_tier, new_tier),
        )
        self._history.append(event)
        logger.info("GROWTH: %s", event.description)
        self._current_tier = new_tier
        return event

    def get_growth_report(self) -> str:
        """Return a human-readable summary of growth status."""
        tier = self._current_tier
        model = self.inventory.get_recommended_model() or "(none — local only)"
        ctx = self.inventory.get_context_budget()
        lines = [
            f"Current Tier : {tier.name} (level {tier.value})",
            f"Model        : {model}",
            f"Context      : {ctx:,} tokens",
            f"API keys     : {len(self.inventory.api_keys)}",
            f"SSH hosts    : {len(self.inventory.ssh_hosts)}",
            f"Emails       : {len(self.inventory.emails)}",
            f"Upgrades     : {len(self._history)}",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _describe_upgrade(old: Tier, new: Tier) -> str:
        direction = "Upgraded" if new > old else "Downgraded"
        old_models = TIER_MODELS.get(old, [])
        new_models = TIER_MODELS.get(new, [])
        old_name = old_models[0] if old_models else "local"
        new_name = new_models[0] if new_models else "local"
        return (
            f"{direction} from Tier {old.value} ({old.name}) to "
            f"Tier {new.value} ({new.name}). "
            f"Model: {old_name} → {new_name}. "
            f"Context: {TIER_CONTEXT_SIZES[old]:,} → "
            f"{TIER_CONTEXT_SIZES[new]:,} tokens."
        )
