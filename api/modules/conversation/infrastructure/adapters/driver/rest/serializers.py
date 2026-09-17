from rest_framework import serializers


class WebhookSerializer(serializers.Serializer):
    channel = serializers.CharField()
    channel_identity = serializers.CharField()
    content = serializers.CharField()
    external_message_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class AgentMessageSerializer(serializers.Serializer):
    """Inbound agent message from a channel driver (Studio, HTTP, later WhatsApp).

    Identity is resolved by the driver, never by a model: the caller supplies the
    channel thread and the business, and the backend resolves the conversation.
    """

    # Optional: when omitted/"default" the single configured business is used.
    business_config_id = serializers.CharField(required=False, allow_blank=True, default="default")
    channel = serializers.CharField(default="LANGSMITH")
    external_thread_id = serializers.CharField()
    content = serializers.CharField()
    external_message_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    client_id = serializers.UUIDField(required=False, allow_null=True)
