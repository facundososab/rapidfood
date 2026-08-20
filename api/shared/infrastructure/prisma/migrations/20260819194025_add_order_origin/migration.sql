-- CreateEnum
CREATE TYPE "OrderOrigin" AS ENUM ('IN_PLACE', 'AGENT');

-- AlterTable
ALTER TABLE "order" ADD COLUMN     "origin" "OrderOrigin" NOT NULL DEFAULT 'IN_PLACE';
