-- Conversation agent foundations.
-- Additive except: (1) conversation.business_config_id becomes required after a
-- defensive backfill, (2) payment external_id/preference_id lose their global
-- unique indexes (external_id becomes unique per provider).

-- DropIndex
DROP INDEX "payment_external_id_key";

-- DropIndex
DROP INDEX "payment_preference_id_key";

-- AlterTable conversation: add columns nullable first so we can backfill.
ALTER TABLE "conversation" ADD COLUMN     "business_config_id" UUID,
ADD COLUMN     "external_thread_id" TEXT;

-- Backfill: associate pre-existing conversations with the single business
-- configuration. No-op when the table is empty (the current state).
UPDATE "conversation"
SET "business_config_id" = (
  SELECT "business_id" FROM "business_configuration" ORDER BY "business_id" LIMIT 1
)
WHERE "business_config_id" IS NULL;

-- Enforce the required business scope now that every row is backfilled.
ALTER TABLE "conversation" ALTER COLUMN "business_config_id" SET NOT NULL;

-- AlterTable order: monotonic commercial snapshot version.
ALTER TABLE "order" ADD COLUMN     "version" INTEGER NOT NULL DEFAULT 0;

-- AlterTable payment: attempt semantics + provider idempotency keys.
ALTER TABLE "payment" ADD COLUMN     "cancel_idempotency_key" TEXT,
ADD COLUMN     "cancellation_status" TEXT,
ADD COLUMN     "create_idempotency_key" TEXT,
ADD COLUMN     "order_version" INTEGER,
ADD COLUMN     "superseded_at" TIMESTAMP(3);

-- CreateTable
CREATE TABLE "idempotent_operation" (
    "idempotent_operation_id" UUID NOT NULL,
    "business_config_id" UUID NOT NULL,
    "idempotency_key" TEXT NOT NULL,
    "operation_name" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'COMPLETED',
    "result" JSONB,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "idempotent_operation_pkey" PRIMARY KEY ("idempotent_operation_id")
);

-- CreateIndex
CREATE INDEX "idempotent_operation_business_config_id_operation_name_idx" ON "idempotent_operation"("business_config_id", "operation_name");

-- CreateIndex
CREATE UNIQUE INDEX "idempotent_operation_business_config_id_idempotency_key_key" ON "idempotent_operation"("business_config_id", "idempotency_key");

-- CreateIndex
CREATE INDEX "conversation_business_config_id_channel_idx" ON "conversation"("business_config_id", "channel");

-- CreateIndex
CREATE UNIQUE INDEX "conversation_business_config_id_channel_external_thread_id_key" ON "conversation"("business_config_id", "channel", "external_thread_id");

-- CreateIndex
CREATE INDEX "payment_order_id_order_version_idx" ON "payment"("order_id", "order_version");

-- CreateIndex
CREATE UNIQUE INDEX "payment_provider_external_id_key" ON "payment"("provider", "external_id");

-- AddForeignKey
ALTER TABLE "conversation" ADD CONSTRAINT "conversation_business_config_id_fkey" FOREIGN KEY ("business_config_id") REFERENCES "business_configuration"("business_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "idempotent_operation" ADD CONSTRAINT "idempotent_operation_business_config_id_fkey" FOREIGN KEY ("business_config_id") REFERENCES "business_configuration"("business_id") ON DELETE RESTRICT ON UPDATE CASCADE;
