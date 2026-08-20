/*
  Warnings:

  - Added the required column `name` to the `product` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "product" ADD COLUMN     "name" TEXT NOT NULL DEFAULT '';

-- Existing rows: backfill name from the current description (legacy products
-- only had one text field acting as both name and description).
UPDATE "product" SET "name" = "description" WHERE "name" = '';

-- Remove the temporary default so the schema matches the Prisma model.
ALTER TABLE "product" ALTER COLUMN "name" DROP DEFAULT;