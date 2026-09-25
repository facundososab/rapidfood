import json

import pytest
from django.core.signing import Signer

from modules.mercadopago.domain.errors.mercadopago_errors import MercadoPagoStateError
from modules.mercadopago.infrastructure.adapters.driven.mercadopago.mercadopago_state_signer import (
    STATE_SALT,
    DjangoStateSigner,
)

SECRET = "unit-test-django-secret"
BUSINESS_CONFIG_ID = "11111111-1111-1111-1111-111111111111"
ISSUED_AT = 1_700_000_000.0


def make_signer(clock=None, **overrides) -> DjangoStateSigner:
    values = {"key": SECRET}
    values.update(overrides)
    if clock is not None:
        values["clock"] = clock
    return DjangoStateSigner(**values)


def test_signs_and_unsigns_the_business_config_id():
    signer = make_signer()

    state = signer.sign(BUSINESS_CONFIG_ID)

    assert state != BUSINESS_CONFIG_ID
    assert make_signer().unsign(state) == BUSINESS_CONFIG_ID


def test_signed_payload_carries_the_business_id_and_timestamp():
    signer = make_signer(clock=lambda: ISSUED_AT)

    payload = json.loads(
        Signer(key=SECRET, salt=STATE_SALT).unsign(signer.sign(BUSINESS_CONFIG_ID))
    )

    assert payload["business_config_id"] == BUSINESS_CONFIG_ID
    assert payload["ts"] == int(ISSUED_AT)


@pytest.mark.parametrize(
    "tampered_state",
    [
        "not-a-signed-state",
        "abc.def.ghi",
        "",
    ],
)
def test_rejects_unsigned_or_malformed_states(tampered_state):
    with pytest.raises(MercadoPagoStateError, match="invalid"):
        make_signer().unsign(tampered_state)


def test_rejects_a_state_signed_with_another_secret():
    foreign_state = DjangoStateSigner(key="another-secret").sign(BUSINESS_CONFIG_ID)

    with pytest.raises(MercadoPagoStateError, match="invalid"):
        make_signer().unsign(foreign_state)


def test_rejects_a_state_with_a_tampered_payload():
    state = make_signer().sign(BUSINESS_CONFIG_ID)
    payload, _, signature = state.partition(":")

    with pytest.raises(MercadoPagoStateError, match="invalid"):
        make_signer().unsign(f"{payload}:{signature[:-1]}x")


def test_accepts_a_state_inside_the_tolerance_window():
    now = {"value": ISSUED_AT}
    signer = make_signer(clock=lambda: now["value"], max_age_seconds=600)
    state = signer.sign(BUSINESS_CONFIG_ID)

    now["value"] = ISSUED_AT + 599

    assert signer.unsign(state) == BUSINESS_CONFIG_ID


def test_rejects_an_expired_state():
    now = {"value": ISSUED_AT}
    signer = make_signer(clock=lambda: now["value"], max_age_seconds=600)
    state = signer.sign(BUSINESS_CONFIG_ID)

    now["value"] = ISSUED_AT + 601

    with pytest.raises(MercadoPagoStateError, match="expired"):
        signer.unsign(state)
