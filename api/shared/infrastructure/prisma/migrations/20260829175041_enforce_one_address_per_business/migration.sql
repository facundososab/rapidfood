/*
  Warnings:

  - A unique constraint covering the columns `[business_config_id]` on the table `address` will be added. If there are existing duplicate values, this will fail.

*/
-- CreateIndex
CREATE UNIQUE INDEX "address_business_config_id_key" ON "address"("business_config_id");
