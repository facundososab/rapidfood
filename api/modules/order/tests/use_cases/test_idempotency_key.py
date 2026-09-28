"""Channel-neutral idempotency key derivation."""
from modules.order.application.idempotency_key import (
    build_idempotency_key,
    canonical_args_hash,
)


def _key(**overrides):
    base = dict(
        business_config_id="biz-1",
        conversation_id="conv-1",
        external_message_id="msg-1",
        operation_name="add_item",
        args={"product_variant_id": "v-1", "quantity": 1},
    )
    base.update(overrides)
    return build_idempotency_key(**base)


def test_argument_order_does_not_change_the_hash():
    assert canonical_args_hash({"a": 1, "b": 2}) == canonical_args_hash({"b": 2, "a": 1})


def test_argument_order_does_not_change_the_key():
    first = _key(args={"product_variant_id": "v-1", "quantity": 1})
    second = _key(args={"quantity": 1, "product_variant_id": "v-1"})
    assert first == second


def test_same_logical_operation_is_stable_across_retries():
    assert _key() == _key()


def test_different_operation_name_does_not_collide():
    assert _key(operation_name="add_item") != _key(operation_name="set_delivery")


def test_different_external_message_does_not_collide():
    assert _key(external_message_id="msg-1") != _key(external_message_id="msg-2")


def test_different_arguments_do_not_collide():
    assert _key(args={"quantity": 1}) != _key(args={"quantity": 2})


def test_different_business_does_not_collide():
    assert _key(business_config_id="biz-1") != _key(business_config_id="biz-2")


def test_no_run_id_like_input_is_accepted():
    import inspect

    params = inspect.signature(build_idempotency_key).parameters
    assert "run_id" not in params
