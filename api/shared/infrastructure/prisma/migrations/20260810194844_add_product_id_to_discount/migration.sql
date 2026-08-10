-- AlterTable
ALTER TABLE "discount" ADD COLUMN     "product_id" UUID;

-- AddForeignKey
ALTER TABLE "discount" ADD CONSTRAINT "discount_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "product"("product_id") ON DELETE CASCADE ON UPDATE CASCADE;
