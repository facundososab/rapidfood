-- Mercado Pago account linking: one credential row per business.

CREATE TABLE "mercadopago_credential" (
    "mercadopago_credential_id" UUID NOT NULL,
    "business_config_id" UUID NOT NULL,
    "access_token" TEXT NOT NULL,
    "refresh_token" TEXT,
    "user_id" TEXT,
    "public_key" TEXT,
    "live_mode" BOOLEAN NOT NULL DEFAULT false,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "mercadopago_credential_pkey" PRIMARY KEY ("mercadopago_credential_id")
);

CREATE UNIQUE INDEX "mercadopago_credential_business_config_id_key" ON "mercadopago_credential"("business_config_id");

ALTER TABLE "mercadopago_credential"
ADD CONSTRAINT "mercadopago_credential_business_config_id_fkey"
FOREIGN KEY ("business_config_id")
REFERENCES "business_configuration"("business_id")
ON DELETE CASCADE ON UPDATE CASCADE;