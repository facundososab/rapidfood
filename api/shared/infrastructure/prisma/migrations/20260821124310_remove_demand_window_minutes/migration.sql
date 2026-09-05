/*
  Warnings:

  - You are about to drop the column `demand_window_minutes` on the `delivery_pricing_configuration` table. All the data in the column will be lost.

*/
-- AlterTable
ALTER TABLE "delivery_pricing_configuration" DROP COLUMN "demand_window_minutes";
