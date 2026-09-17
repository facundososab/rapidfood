-- AlterTable
ALTER TABLE "order"
ADD COLUMN "delivery_street" TEXT,
ADD COLUMN "delivery_street_number" TEXT,
ADD COLUMN "delivery_floor" TEXT,
ADD COLUMN "delivery_apartment" TEXT,
ADD COLUMN "delivery_city" TEXT,
ADD COLUMN "delivery_province" TEXT,
ADD COLUMN "delivery_postal_code" TEXT,
ADD COLUMN "coupon_code" TEXT;
