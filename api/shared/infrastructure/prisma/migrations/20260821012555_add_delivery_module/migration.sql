/*
  Warnings:

  - The `available_zone` column on the `business_configuration` table would be dropped and recreated. This will lead to data loss if there is data in the column.

*/
-- AlterTable
ALTER TABLE "business_configuration" DROP COLUMN "available_zone",
ADD COLUMN     "available_zone" JSONB;

-- AlterTable
ALTER TABLE "coupon" ADD COLUMN     "is_active" BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN     "min_order_amount" DECIMAL(10,2);

-- AlterTable
ALTER TABLE "order" ADD COLUMN     "business_config_id" UUID;

-- CreateTable
CREATE TABLE "delivery_pricing_configuration" (
    "delivery_pricing_configuration_id" UUID NOT NULL,
    "business_config_id" UUID NOT NULL,
    "origin_address_id" UUID NOT NULL,
    "price_per_km" DECIMAL(10,2) NOT NULL,
    "high_demand_threshold" INTEGER NOT NULL,
    "very_high_demand_threshold" INTEGER NOT NULL,
    "high_demand_multiplier" DECIMAL(5,2) NOT NULL,
    "very_high_demand_multiplier" DECIMAL(5,2) NOT NULL,
    "demand_window_minutes" INTEGER NOT NULL,

    CONSTRAINT "delivery_pricing_configuration_pkey" PRIMARY KEY ("delivery_pricing_configuration_id")
);

-- CreateTable
CREATE TABLE "delivery_weekday_pricing_rule" (
    "delivery_weekday_pricing_rule_id" UUID NOT NULL,
    "delivery_pricing_config_id" UUID NOT NULL,
    "week_day" "WeekDay" NOT NULL,
    "multiplier" DECIMAL(5,2) NOT NULL,

    CONSTRAINT "delivery_weekday_pricing_rule_pkey" PRIMARY KEY ("delivery_weekday_pricing_rule_id")
);

-- CreateIndex
CREATE UNIQUE INDEX "delivery_pricing_configuration_business_config_id_key" ON "delivery_pricing_configuration"("business_config_id");

-- CreateIndex
CREATE UNIQUE INDEX "delivery_pricing_configuration_origin_address_id_key" ON "delivery_pricing_configuration"("origin_address_id");

-- CreateIndex
CREATE UNIQUE INDEX "delivery_weekday_pricing_rule_delivery_pricing_config_id_we_key" ON "delivery_weekday_pricing_rule"("delivery_pricing_config_id", "week_day");

-- CreateIndex
CREATE INDEX "order_business_config_id_delivery_type_status_created_at_idx" ON "order"("business_config_id", "delivery_type", "status", "created_at");

-- AddForeignKey
ALTER TABLE "order" ADD CONSTRAINT "order_business_config_id_fkey" FOREIGN KEY ("business_config_id") REFERENCES "business_configuration"("business_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "delivery_pricing_configuration" ADD CONSTRAINT "delivery_pricing_configuration_business_config_id_fkey" FOREIGN KEY ("business_config_id") REFERENCES "business_configuration"("business_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "delivery_pricing_configuration" ADD CONSTRAINT "delivery_pricing_configuration_origin_address_id_fkey" FOREIGN KEY ("origin_address_id") REFERENCES "address"("address_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "delivery_weekday_pricing_rule" ADD CONSTRAINT "delivery_weekday_pricing_rule_delivery_pricing_config_id_fkey" FOREIGN KEY ("delivery_pricing_config_id") REFERENCES "delivery_pricing_configuration"("delivery_pricing_configuration_id") ON DELETE CASCADE ON UPDATE CASCADE;
