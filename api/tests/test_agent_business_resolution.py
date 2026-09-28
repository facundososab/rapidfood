"""Resolver for the agent's business id (composition root).

The business row id is a generated UUID: re-seeding the database creates a NEW
id, so a hardcoded environment value can go stale. The resolver must prefer an
explicit id, validate it, and fall back to the single configured business.
"""
from types import SimpleNamespace

import pytest

from composition.container import resolve_agent_business_config_id


class FakeGetConfiguration:
    def __init__(self, by_id=None, default=None):
        self.by_id = by_id or {}
        self.default = default
        self.ids = []

    def execute(self, query):
        self.ids.append(query.business_config_id)
        if query.business_config_id == "default":
            if self.default is None:
                raise RuntimeError("BusinessConfiguration 'default' not found.")
            return {"id": self.default}
        value = self.by_id.get(query.business_config_id)
        if value is None:
            raise RuntimeError(f"BusinessConfiguration '{query.business_config_id}' not found.")
        return {"id": value}


@pytest.fixture
def business(monkeypatch):
    container = SimpleNamespace(get_configuration=FakeGetConfiguration(by_id={"biz-1": "biz-1"}, default="single-biz"))
    monkeypatch.setattr(
        "composition.container.get_app_business_container", lambda: container
    )
    return container


def test_explicit_id_is_validated_and_returned(business):
    assert resolve_agent_business_config_id("biz-1") == "biz-1"
    assert business.get_configuration.ids == ["biz-1"]


def test_stale_explicit_id_falls_back_to_the_single_business(business):
    # A re-seed invalidated the old id: never write it as a foreign key.
    assert resolve_agent_business_config_id("stale-uuid") == "single-biz"
    assert business.get_configuration.ids == ["stale-uuid", "default"]


def test_default_maps_to_the_single_business(business):
    assert resolve_agent_business_config_id("default") == "single-biz"


def test_missing_everything_raises_a_clear_error(monkeypatch):
    container = SimpleNamespace(get_configuration=FakeGetConfiguration(by_id={}, default=None))
    monkeypatch.setattr(
        "composition.container.get_app_business_container", lambda: container
    )
    with pytest.raises(RuntimeError, match="No business configuration found"):
        resolve_agent_business_config_id(None)


def test_env_fallback_is_used_when_nothing_is_passed(monkeypatch, business):
    monkeypatch.setattr(
        "django.conf.settings.AGENT_BUSINESS_CONFIG_ID", "biz-1", raising=False
    )
    assert resolve_agent_business_config_id(None) == "biz-1"
