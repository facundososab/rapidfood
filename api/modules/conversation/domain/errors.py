class ConversationDomainError(ValueError):
    """Base error for conversation domain validation."""


class ConversationValidationError(ConversationDomainError):
    """Raised when a conversation violates domain invariants."""


class MessageValidationError(ConversationDomainError):
    """Raised when a message violates domain invariants."""
