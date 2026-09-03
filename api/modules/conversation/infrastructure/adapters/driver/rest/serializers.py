from rest_framework import serializers


class WebhookSerializer(serializers.Serializer):
    channel = serializers.CharField()
    channel_identity = serializers.CharField()
    content = serializers.CharField()
    external_message_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

