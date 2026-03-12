"""Tests for charonos.growth (resource_tracker + self_improve)."""

from charonos.growth.resource_tracker import (
    BOOTSTRAP_MODEL,
    ResourceInventory,
    Tier,
    TIER_MODELS,
    build_inventory_from_config,
)
from charonos.growth.self_improve import GrowthEngine
from charonos.config import CharonConfig, OpenRouterConfig, DeepSeekConfig


# ---- ResourceInventory ----

def test_empty_inventory_is_local():
    inv = ResourceInventory()
    assert inv.compute_tier() == Tier.LOCAL


def test_one_key_is_small():
    inv = ResourceInventory(api_keys=["k1"])
    assert inv.compute_tier() == Tier.SMALL


def test_two_keys_is_medium():
    inv = ResourceInventory(api_keys=["k1", "k2"])
    assert inv.compute_tier() == Tier.MEDIUM


def test_one_ssh_host_is_medium():
    inv = ResourceInventory(api_keys=["k1"], ssh_hosts=["h1"])
    assert inv.compute_tier() == Tier.MEDIUM


def test_frontier_tier():
    inv = ResourceInventory(
        api_keys=["k1", "k2", "k3", "k4"],
        ssh_hosts=["h1", "h2"],
    )
    assert inv.compute_tier() == Tier.FRONTIER


def test_bootstrap_model_is_dolphin_mistral():
    assert "dolphin-mistral" in BOOTSTRAP_MODEL


def test_small_tier_starts_with_dolphin():
    models = TIER_MODELS[Tier.SMALL]
    assert models[0] == BOOTSTRAP_MODEL


def test_recommended_model_for_small():
    inv = ResourceInventory(api_keys=["k1"])
    model = inv.get_recommended_model()
    assert model == BOOTSTRAP_MODEL


def test_recommended_model_for_local_is_none():
    inv = ResourceInventory()
    assert inv.get_recommended_model() is None


def test_add_api_key_deduplicates():
    inv = ResourceInventory()
    inv.add_api_key("k1")
    inv.add_api_key("k1")
    assert len(inv.api_keys) == 1


def test_add_ssh_host():
    inv = ResourceInventory()
    inv.add_ssh_host("h1")
    assert inv.ssh_hosts == ["h1"]


def test_add_email():
    inv = ResourceInventory()
    inv.add_email("a@b.com")
    assert inv.emails == ["a@b.com"]


def test_build_from_config():
    cfg = CharonConfig(
        openrouter=OpenRouterConfig(api_key="or"),
        deepseek=DeepSeekConfig(api_key="ds", email="e@x.com"),
        extra_api_keys=["ex1"],
        extra_emails=["f@g.com"],
    )
    inv = build_inventory_from_config(cfg)
    assert len(inv.api_keys) == 3
    assert len(inv.emails) == 2


# ---- GrowthEngine ----

def test_growth_no_change():
    inv = ResourceInventory(api_keys=["k1"])
    engine = GrowthEngine(inv)
    assert engine.check_for_upgrade() is None


def test_growth_upgrade():
    inv = ResourceInventory(api_keys=["k1"])
    engine = GrowthEngine(inv)
    assert engine.current_tier == Tier.SMALL

    # Add resources to trigger an upgrade
    inv.add_api_key("k2")
    evt = engine.check_for_upgrade()

    assert evt is not None
    assert evt.new_tier == Tier.MEDIUM
    assert engine.current_tier == Tier.MEDIUM
    assert len(engine.history) == 1


def test_growth_report():
    inv = ResourceInventory(api_keys=["k1"])
    engine = GrowthEngine(inv)
    report = engine.get_growth_report()
    assert "SMALL" in report
    assert "dolphin-mistral" in report
