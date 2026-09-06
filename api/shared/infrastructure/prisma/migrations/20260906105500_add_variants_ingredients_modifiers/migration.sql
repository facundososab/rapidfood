-- DropForeignKey
ALTER TABLE "order_line" DROP CONSTRAINT "order_line_product_id_fkey";

-- DropForeignKey
ALTER TABLE "price" DROP CONSTRAINT "price_product_id_fkey";

-- DropIndex
DROP INDEX "order_line_order_id_product_id_key";

-- DropIndex
DROP INDEX "order_line_product_id_idx";

-- DropIndex
DROP INDEX "price_product_id_since_date_idx";

-- CreateTable
CREATE TABLE "client_address" (
    "client_address_id" UUID NOT NULL,
    "client_id" UUID NOT NULL,
    "street" TEXT NOT NULL,
    "street_number" TEXT NOT NULL,
    "floor" TEXT,
    "apartment" TEXT,
    "city" TEXT NOT NULL,
    "province" TEXT NOT NULL,
    "postal_code" TEXT,
    "latitude" DECIMAL(10,7) NOT NULL,
    "longitude" DECIMAL(10,7) NOT NULL,
    "delivery_instructions" TEXT,
    "label" TEXT,
    "is_default" BOOLEAN NOT NULL DEFAULT false,

    CONSTRAINT "client_address_pkey" PRIMARY KEY ("client_address_id")
);

-- CreateTable
CREATE TABLE "product_variant" (
    "product_variant_id" UUID NOT NULL,
    "product_id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "available" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "product_variant_pkey" PRIMARY KEY ("product_variant_id")
);

-- CreateTable
CREATE TABLE "ingredient" (
    "ingredient_id" UUID NOT NULL,
    "name" TEXT NOT NULL,

    CONSTRAINT "ingredient_pkey" PRIMARY KEY ("ingredient_id")
);

-- CreateTable
CREATE TABLE "product_variant_ingredient" (
    "product_variant_ingredient_id" UUID NOT NULL,
    "product_variant_id" UUID NOT NULL,
    "ingredient_id" UUID NOT NULL,
    "removable" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "product_variant_ingredient_pkey" PRIMARY KEY ("product_variant_ingredient_id")
);

-- CreateTable
CREATE TABLE "modifier_group" (
    "modifier_group_id" UUID NOT NULL,
    "product_id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "min_selections" INTEGER NOT NULL DEFAULT 0,
    "max_selections" INTEGER NOT NULL,

    CONSTRAINT "modifier_group_pkey" PRIMARY KEY ("modifier_group_id")
);

-- CreateTable
CREATE TABLE "modifier_option" (
    "modifier_option_id" UUID NOT NULL,
    "modifier_group_id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "price_delta" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "available" BOOLEAN NOT NULL DEFAULT true,

    CONSTRAINT "modifier_option_pkey" PRIMARY KEY ("modifier_option_id")
);

-- CreateTable
CREATE TABLE "order_line_modifier" (
    "order_line_modifier_id" UUID NOT NULL,
    "order_line_id" UUID NOT NULL,
    "modifier_option_id" UUID NOT NULL,
    "option_name_snapshot" TEXT NOT NULL,
    "price_delta" DECIMAL(10,2),

    CONSTRAINT "order_line_modifier_pkey" PRIMARY KEY ("order_line_modifier_id")
);

-- CreateTable
CREATE TABLE "order_line_removed_ingredient" (
    "order_line_removed_ingredient_id" UUID NOT NULL,
    "order_line_id" UUID NOT NULL,
    "ingredient_id" UUID NOT NULL,
    "ingredient_name_snapshot" TEXT NOT NULL,

    CONSTRAINT "order_line_removed_ingredient_pkey" PRIMARY KEY ("order_line_removed_ingredient_id")
);

-- CreateIndex
CREATE INDEX "client_address_client_id_idx" ON "client_address"("client_id");

-- CreateIndex
CREATE INDEX "product_variant_product_id_idx" ON "product_variant"("product_id");

-- CreateIndex
CREATE INDEX "product_variant_ingredient_ingredient_id_idx" ON "product_variant_ingredient"("ingredient_id");

-- CreateIndex
CREATE UNIQUE INDEX "product_variant_ingredient_product_variant_id_ingredient_id_key" ON "product_variant_ingredient"("product_variant_id", "ingredient_id");

-- CreateIndex
CREATE INDEX "modifier_group_product_id_idx" ON "modifier_group"("product_id");

-- CreateIndex
CREATE INDEX "modifier_option_modifier_group_id_idx" ON "modifier_option"("modifier_group_id");

-- CreateIndex
CREATE INDEX "order_line_modifier_modifier_option_id_idx" ON "order_line_modifier"("modifier_option_id");

-- CreateIndex
CREATE UNIQUE INDEX "order_line_modifier_order_line_id_modifier_option_id_key" ON "order_line_modifier"("order_line_id", "modifier_option_id");

-- CreateIndex
CREATE INDEX "order_line_removed_ingredient_ingredient_id_idx" ON "order_line_removed_ingredient"("ingredient_id");

-- CreateIndex
CREATE UNIQUE INDEX "order_line_removed_ingredient_order_line_id_ingredient_id_key" ON "order_line_removed_ingredient"("order_line_id", "ingredient_id");

-- CreateIndex
CREATE INDEX "discount_product_id_idx" ON "discount"("product_id");


-- AlterTable (Add Columns as Nullable)
ALTER TABLE "discount" ADD COLUMN     "product_variant_id" UUID;
ALTER TABLE "order_line" ADD COLUMN     "product_variant_id" UUID;
ALTER TABLE "price" ADD COLUMN     "product_variant_id" UUID;

-- CreateIndex
CREATE INDEX "discount_product_variant_id_idx" ON "discount"("product_variant_id");

-- CreateIndex
CREATE INDEX "order_line_product_variant_id_idx" ON "order_line"("product_variant_id");

-- CreateIndex
CREATE INDEX "price_product_variant_id_since_date_idx" ON "price"("product_variant_id", "since_date");


-- Backfill SQL
INSERT INTO product_variant (product_variant_id, product_id, name, available)
SELECT
    gen_random_uuid(),
    product_id,
    'Default',
    available
FROM product;

UPDATE price
SET product_variant_id = pv.product_variant_id
FROM product_variant pv
WHERE price.product_id = pv.product_id;

UPDATE order_line
SET product_variant_id = pv.product_variant_id
FROM product_variant pv
WHERE order_line.product_id = pv.product_id;

-- AlterTable (Set Not Null)
ALTER TABLE "order_line" ALTER COLUMN "product_variant_id" SET NOT NULL;
ALTER TABLE "price" ALTER COLUMN "product_variant_id" SET NOT NULL;

-- AlterTable (Drop Column)
ALTER TABLE "order_line" DROP COLUMN "product_id";
ALTER TABLE "price" DROP COLUMN "product_id";



-- AddForeignKey
ALTER TABLE "client_address" ADD CONSTRAINT "client_address_client_id_fkey" FOREIGN KEY ("client_id") REFERENCES "client"("client_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_line" ADD CONSTRAINT "order_line_product_variant_id_fkey" FOREIGN KEY ("product_variant_id") REFERENCES "product_variant"("product_variant_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "price" ADD CONSTRAINT "price_product_variant_id_fkey" FOREIGN KEY ("product_variant_id") REFERENCES "product_variant"("product_variant_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "discount" ADD CONSTRAINT "discount_product_variant_id_fkey" FOREIGN KEY ("product_variant_id") REFERENCES "product_variant"("product_variant_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "product_variant" ADD CONSTRAINT "product_variant_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "product"("product_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "product_variant_ingredient" ADD CONSTRAINT "product_variant_ingredient_product_variant_id_fkey" FOREIGN KEY ("product_variant_id") REFERENCES "product_variant"("product_variant_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "product_variant_ingredient" ADD CONSTRAINT "product_variant_ingredient_ingredient_id_fkey" FOREIGN KEY ("ingredient_id") REFERENCES "ingredient"("ingredient_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "modifier_group" ADD CONSTRAINT "modifier_group_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "product"("product_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "modifier_option" ADD CONSTRAINT "modifier_option_modifier_group_id_fkey" FOREIGN KEY ("modifier_group_id") REFERENCES "modifier_group"("modifier_group_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_line_modifier" ADD CONSTRAINT "order_line_modifier_order_line_id_fkey" FOREIGN KEY ("order_line_id") REFERENCES "order_line"("order_line_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_line_modifier" ADD CONSTRAINT "order_line_modifier_modifier_option_id_fkey" FOREIGN KEY ("modifier_option_id") REFERENCES "modifier_option"("modifier_option_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_line_removed_ingredient" ADD CONSTRAINT "order_line_removed_ingredient_order_line_id_fkey" FOREIGN KEY ("order_line_id") REFERENCES "order_line"("order_line_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_line_removed_ingredient" ADD CONSTRAINT "order_line_removed_ingredient_ingredient_id_fkey" FOREIGN KEY ("ingredient_id") REFERENCES "ingredient"("ingredient_id") ON DELETE RESTRICT ON UPDATE CASCADE;

