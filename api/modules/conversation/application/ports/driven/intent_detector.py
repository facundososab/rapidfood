from __future__ import annotations

from typing import Protocol, runtime_checkable

from modules.conversation.domain.value_objects import DetectedIntent


@runtime_checkable
class IntentDetectorPort(Protocol):
    def detect(self, content: str) -> DetectedIntent: ...
