-- AlterTable
ALTER TABLE "coupon" ADD COLUMN     "is_active" BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN     "min_order_amount" DECIMAL(10,2);
