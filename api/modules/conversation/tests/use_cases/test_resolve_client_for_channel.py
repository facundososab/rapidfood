from modules.conversation.application.use_cases.resolve_client_for_channel import (
    ResolveClientForChannelUseCase,
)


class FakeClientService:
    def __init__(self, result="client-1"):
        self.result = result
        self.calls = []

    def resolve_client(self, full_name, phone_number=None):
        self.calls.append((full_name, phone_number))
        return self.result


def test_resolves_a_client_from_name_and_phone():
    service = FakeClientService()
    assert (
        ResolveClientForChannelUseCase(service).execute("Facundo Sosa", "5493413531061")
        == "client-1"
    )
    assert service.calls == [("Facundo Sosa", "5493413531061")]


def test_returns_none_without_service_or_phone():
    assert ResolveClientForChannelUseCase(None).execute("x", "549") is None
    assert ResolveClientForChannelUseCase(FakeClientService()).execute("x", None) is None


def test_never_raises_on_resolution_failure():
    class Boom:
        def resolve_client(self, full_name, phone_number=None):
            raise RuntimeError("boom")

    assert ResolveClientForChannelUseCase(Boom()).execute("x", "549") is None
