ALTER TABLE "payment"
ADD COLUMN "preference_id" TEXT,
ADD COLUMN "checkout_url" TEXT,
ADD COLUMN "external_reference" TEXT,
ADD COLUMN "provider_payload" JSONB,
ADD COLUMN "expires_at" TIMESTAMP(3);

CREATE UNIQUE INDEX "payment_external_id_key" ON "payment"("external_id");
CREATE UNIQUE INDEX "payment_preference_id_key" ON "payment"("preference_id");
CREATE INDEX "payment_external_reference_idx" ON "payment"("external_reference");
