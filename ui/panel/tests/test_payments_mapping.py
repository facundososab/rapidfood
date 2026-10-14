"""The payments HTTP client maps the backend payload (snake_case) correctly."""
from panel.services.http_client import HttpRapidfoodClient


def test_payment_mapper_reads_snake_case_fields():
    client = HttpRapidfoodClient("http://api", session=object())

    payment = client._payment(
        {
            "id": "p1",
            "order_id": "o1",
            "provider": "MERCADOPAGO",
            "status": "APPROVED",
            "amount": "100.00",
            "external_id": "EXT-1",
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T01:00:00",
        }
    )

    assert payment.id == "p1"
    assert payment.orderId == "o1"
    assert payment.status == "APPROVED"
    assert payment.externalId == "EXT-1"
    assert payment.createdAt is not None
