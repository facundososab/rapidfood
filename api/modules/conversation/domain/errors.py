class ConversationDomainError(ValueError):
    """Base error for conversation domain validation."""


class ConversationValidationError(ConversationDomainError):
    """Raised when a conversation violates domain invariants."""


class ConversationNotFoundError(ConversationDomainError):
    """Raised when a conversation id does not exist."""


class MessageValidationError(ConversationDomainError):
    """Raised when a message violates domain invariants."""


class AgentBusinessError(ConversationDomainError):
    """A business outcome the agent can explain to the customer.

    Distinct from a technical failure: the agent must not present a provider
    outage as "we don't deliver there", and vice versa.
    """

    code = "AGENT_BUSINESS_ERROR"

    def __init__(self, message: str = "", *, code: str | None = None) -> None:
        super().__init__(message or self.__class__.__name__)
        if code:
            self.code = code


class NewOrderRequiredError(AgentBusinessError):
    """The previous order cannot be modified; a new order is needed.

    The agent MUST ask the customer before starting a new order (it may imply a
    new delivery and a new shipping cost).
    """

    code = "NEW_ORDER_REQUIRED"


class NoActiveOrderError(AgentBusinessError):
    """An operation needs an order but the conversation has none."""

    code = "NO_ACTIVE_ORDER"


class WhatsAppConfigurationValidationError(ConversationDomainError):
    """Raised when WhatsApp credentials violate domain invariants."""


class WhatsAppConfigurationNotFoundError(ConversationDomainError):
    """Raised when a business has no WhatsApp configuration (or it is inactive)."""


class WhatsAppSendError(RuntimeError):
    """The WhatsApp Cloud API rejected or failed to deliver a message."""

    def __init__(self, message: str = "", *, status_code: int | None = None) -> None:
        super().__init__(message or "WhatsApp send failed")
        self.status_code = status_code


class TranscriptionFailedError(RuntimeError):
    """Inbound audio could not be transcribed (download or STT provider failed)."""
