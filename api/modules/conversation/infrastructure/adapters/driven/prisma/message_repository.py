from __future__ import annotations

from modules.conversation.domain.models.message import Message


class PrismaMessageRepository:
    def __init__(self, client):
        self._client = client

    def add(self, message: Message) -> Message:
        self._client.message.create(
            data={
                "id": message.message_id,
                "conversationId": message.conversation_id,
                "role": message.role.value,
                "content": message.content,
                "detectedIntent": message.detected_intent.value if message.detected_intent else None,
                "sentiment": message.sentiment.value if message.sentiment else None,
                "status": message.status.value if message.status else None,
                "createdAt": message.created_at,
            }
        )
        return message

    def list_by_conversation(self, conversation_id: str) -> list[Message]:
        rows = self._client.message.find_many(where={"conversationId": conversation_id}, order={"createdAt": "asc"})
        return [
            Message(
                message_id=row.id,
                conversation_id=row.conversationId,
                role=row.role,
                content=row.content,
                detected_intent=getattr(row, "detectedIntent", None),
                sentiment=getattr(row, "sentiment", None),
                status=getattr(row, "status", None),
                created_at=getattr(row, "createdAt", None),
            )
            for row in rows
        ]
