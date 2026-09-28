-- AlterTable
-- Both columns are already created by 20260821012555_add_delivery_module, so this
-- migration is a no-op on a fresh database. IF NOT EXISTS keeps the whole
-- migration history replayable from scratch instead of failing the second time.
ALTER TABLE "coupon" ADD COLUMN IF NOT EXISTS "is_active" BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN IF NOT EXISTS "min_order_amount" DECIMAL(10,2);
