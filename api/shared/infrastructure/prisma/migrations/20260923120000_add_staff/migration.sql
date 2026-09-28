-- Auth module: restaurant staff (Supabase Auth identity + role in our DB).

CREATE TYPE "StaffRole" AS ENUM ('ADMIN', 'CASHIER', 'KITCHEN');

CREATE TABLE "staff" (
    "staff_id" UUID NOT NULL,
    "supabase_auth_id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "role" "StaffRole" NOT NULL DEFAULT 'CASHIER',
    "business_config_id" UUID,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "staff_pkey" PRIMARY KEY ("staff_id")
);

CREATE UNIQUE INDEX "staff_supabase_auth_id_key" ON "staff"("supabase_auth_id");
CREATE UNIQUE INDEX "staff_email_key" ON "staff"("email");

ALTER TABLE "staff"
ADD CONSTRAINT "staff_business_config_id_fkey"
FOREIGN KEY ("business_config_id")
REFERENCES "business_configuration"("business_id")
ON DELETE SET NULL ON UPDATE CASCADE;