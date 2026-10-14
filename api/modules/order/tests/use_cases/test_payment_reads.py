"""Payment reads for the panel: list (with filters) and detail."""
from decimal import Decimal

from modules.order.application.ports.driver.payment_reads_ports import ListPaymentsQuery
from modules.order.application.use_cases.payment_reads import (
    GetPaymentUseCase,
    ListPaymentsUseCase,
)
from modules.order.domain.models.payment_attempt import PaymentAttempt
from modules.order.domain.models.payment_status import PaymentStatus


class FakePaymentRepo:
    def __init__(self, rows):
        self.rows = list(rows)

    def list_all(self, status=None, provider=None):
        rows = self.rows
        if status is not None:
            rows = [r for r in rows if r.status == status]
        if provider:
            rows = [r for r in rows if r.provider == provider]
        return rows

    def get_by_id(self, payment_id):
        return next((r for r in self.rows if r.id == payment_id), None)


def _payment(pid, status=PaymentStatus.APPROVED, provider="MERCADOPAGO"):
    return PaymentAttempt(
        id=pid, order_id="o-1", provider=provider, amount=Decimal("100"), status=status
    )


def test_list_payments_filters_by_status():
    repo = FakePaymentRepo([_payment("p1"), _payment("p2", status=PaymentStatus.PENDING)])

    rows = ListPaymentsUseCase(repo).execute(ListPaymentsQuery(status="APPROVED"))

    assert [r.id for r in rows] == ["p1"]


def test_list_payments_ignores_an_unknown_status():
    repo = FakePaymentRepo([_payment("p1")])

    rows = ListPaymentsUseCase(repo).execute(ListPaymentsQuery(status="NOT_A_STATUS"))

    assert [r.id for r in rows] == ["p1"]


def test_get_payment_returns_none_when_missing():
    assert GetPaymentUseCase(FakePaymentRepo([])).execute("missing") is None
