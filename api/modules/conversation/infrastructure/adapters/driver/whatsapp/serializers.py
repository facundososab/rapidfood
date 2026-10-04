from rest_framework import serializers


class WhatsAppConfigSerializer(serializers.Serializer):
    """Staff input for a business's WhatsApp credentials.

    Secrets are write-only: on update they may be omitted (blank) and the stored
    value is preserved.
    """

    business_config_id = serializers.CharField(required=False, default="default")
    phone_number_id = serializers.CharField()
    verify_token = serializers.CharField()
    access_token = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )
    app_secret = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=""
    )
    api_version = serializers.CharField(required=False, allow_blank=True, default="v21.0")
    waba_id = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    display_phone_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    order_paid_template_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, default=None
    )
    order_paid_template_lang = serializers.CharField(
        required=False, allow_blank=True, default="es_AR"
    )
    is_active = serializers.BooleanField(required=False, default=True)
