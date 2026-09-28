"""Agent policy: the prompt encodes the rules and the eval dataset is complete.

These are deterministic checks. The LLM-behaviour evals themselves run in
LangSmith/Studio from the dataset in `langchain/evals/agent_policy_scenarios.json`.
"""
import json
import re
from pathlib import Path

from modules.conversation.infrastructure.adapters.driver.langchain.prompt import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
)

_DATASET = (
    Path(__file__).resolve().parents[2]
    / "infrastructure"
    / "adapters"
    / "driver"
    / "langchain"
    / "evals"
    / "agent_policy_scenarios.json"
)


def _normalized() -> str:
    """The prompt is wrapped for readability; collapse whitespace for asserts."""
    return re.sub(r"\s+", " ", SYSTEM_PROMPT).strip().lower()


def test_prompt_speaks_of_order_not_cart():
    lowered = _normalized()
    assert 'nunca de "carrito"' in lowered
    # And never narrates internal operations ("agregué al pedido").
    assert "no narres operaciones internas" in lowered


def test_prompt_forbids_internal_concepts():
    lowered = _normalized()
    assert "nunca menciones conceptos internos" in lowered
    for concept in ('"sistema"', '"base de datos"', '"registrar"', '"tool"'):
        assert concept in lowered


def test_prompt_forbids_inventing_business_facts():
    lowered = _normalized()
    assert "nunca inventes" in lowered
    for fact in ("precios", "disponibilidad", "ingredientes", "totales", "estados"):
        assert fact in lowered


def test_prompt_makes_the_backend_order_the_source_of_truth():
    lowered = _normalized()
    assert "única fuente de verdad" in lowered
    assert "historial de la conversación no lo es" in lowered


def test_prompt_requires_using_tools_for_state():
    assert "usás las herramientas" in _normalized()


def test_prompt_always_states_prices():
    lowered = _normalized()
    assert "siempre que nombres un producto, decí su precio" in lowered
    assert "precio de cada una" in lowered


def test_prompt_mentions_the_coupon_option_at_the_total():
    lowered = _normalized()
    assert "cupón" in lowered
    assert "cuando muestres el total, recordale" in lowered


def test_prompt_asks_for_the_client_name_before_confirming():
    lowered = _normalized()
    assert "antes de confirmar necesitás el nombre" in lowered
    assert "no después de que el cliente confirme" in lowered


def test_prompt_accepts_any_clear_affirmative_as_confirmation():
    lowered = _normalized()
    assert "cualquier respuesta afirmativa clara" in lowered
    assert '"dale"' in lowered
    assert "no exijas la palabra" in lowered


def test_prompt_requires_answering_every_question_before_advancing():
    lowered = _normalized()
    assert "primero respondé todo lo que preguntó" in lowered


def test_prompt_upsells_with_a_concrete_proposal():
    lowered = _normalized()
    assert "ofrecé acompañarlo" in lowered
    assert "no un catálogo" in lowered


def test_prompt_does_not_let_the_model_create_orders_on_new_order_required():
    lowered = _normalized()
    assert "new_order_required" in lowered
    assert "no armes uno nuevo en silencio" in lowered


def test_prompt_only_allows_the_domain_payment_types():
    lowered = _normalized()
    assert "cash" in lowered
    assert "online" in lowered
    for invented in ("MERCADO_PAGO", "TRANSFER", "CARD"):
        assert invented not in SYSTEM_PROMPT


def test_prompt_simplifies_the_delivery_address():
    lowered = _normalized()
    assert "alcanza con la calle y el número" in lowered


def test_prompt_never_leaks_technical_details():
    assert "detalles técnicos" in _normalized()


def test_prompt_is_versioned():
    assert PROMPT_VERSION
    assert PROMPT_VERSION in SYSTEM_PROMPT


def test_eval_dataset_covers_the_required_scenarios():
    dataset = json.loads(_DATASET.read_text(encoding="utf-8"))
    ids = {scenario["id"] for scenario in dataset["scenarios"]}

    assert {
        "menu-question-uses-search",
        "product-question-uses-detail",
        "purchase-intent-adds-item",
        "second-item-is-a-second-line",
        "delivery-question-quotes-only",
        "delivery-request-sets-delivery",
        "bare-yes-does-not-confirm",
        "explicit-confirmation-after-summary-confirms",
    } <= ids

    for scenario in dataset["scenarios"]:
        assert scenario["input"]
        assert "expected_tools" in scenario
        assert "forbidden_tools" in scenario


def test_eval_dataset_encodes_the_confirmation_rule():
    dataset = json.loads(_DATASET.read_text(encoding="utf-8"))
    by_id = {scenario["id"]: scenario for scenario in dataset["scenarios"]}

    assert by_id["bare-yes-does-not-confirm"]["expected_tools"] == []
    assert "confirm_order" in by_id["bare-yes-does-not-confirm"]["forbidden_tools"]
    assert "confirm_order" in by_id["explicit-confirmation-after-summary-confirms"]["expected_tools"]
