-- Per-restaurant WhatsApp Cloud API credentials (1:1 with BusinessConfiguration).
-- Secrets (access token, app secret) are stored encrypted by the application.

CREATE TABLE "whatsapp_configuration" (
    "whatsapp_config_id" UUID NOT NULL,
    "business_config_id" UUID NOT NULL,
    "phone_number_id" TEXT NOT NULL,
    "waba_id" TEXT,
    "display_phone_number" TEXT,
    "verify_token" TEXT NOT NULL,
    "access_token_enc" TEXT NOT NULL,
    "app_secret_enc" TEXT NOT NULL,
    "api_version" TEXT NOT NULL DEFAULT 'v21.0',
    "order_paid_template_name" TEXT,
    "order_paid_template_lang" TEXT DEFAULT 'es_AR',
    "is_active" BOOLEAN NOT NULL DEFAULT true,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "whatsapp_configuration_pkey" PRIMARY KEY ("whatsapp_config_id")
);

CREATE UNIQUE INDEX "whatsapp_configuration_business_config_id_key" ON "whatsapp_configuration"("business_config_id");
CREATE UNIQUE INDEX "whatsapp_configuration_phone_number_id_key" ON "whatsapp_configuration"("phone_number_id");

ALTER TABLE "whatsapp_configuration"
ADD CONSTRAINT "whatsapp_configuration_business_config_id_fkey"
FOREIGN KEY ("business_config_id")
REFERENCES "business_configuration"("business_id")
ON DELETE CASCADE ON UPDATE CASCADE;
