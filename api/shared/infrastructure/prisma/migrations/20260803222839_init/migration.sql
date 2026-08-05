-- CreateEnum
CREATE TYPE "OrderStatus" AS ENUM ('BORRADOR', 'PENDIENTE', 'PAGADO', 'CONFIRMADO', 'EN_PREPARACION', 'LISTO', 'ENTREGADO', 'RETIRADO', 'CANCELADO');

-- CreateEnum
CREATE TYPE "DeliveryType" AS ENUM ('ENVIO', 'RETIRO');

-- CreateEnum
CREATE TYPE "PaymentType" AS ENUM ('EFECTIVO', 'ONLINE');

-- CreateEnum
CREATE TYPE "PaymentStatus" AS ENUM ('PENDIENTE', 'APROBADO', 'RECHAZADO', 'FALLIDO', 'VENCIDO');

-- CreateEnum
CREATE TYPE "WeekDay" AS ENUM ('LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO');

-- CreateTable
CREATE TABLE "business_configuration" (
    "business_id" UUID NOT NULL,
    "business_name" TEXT NOT NULL,
    "min_order" DECIMAL(10,2) NOT NULL,
    "shipping_cost" DECIMAL(10,2) NOT NULL,
    "available_zone" TEXT NOT NULL,

    CONSTRAINT "business_configuration_pkey" PRIMARY KEY ("business_id")
);

-- CreateTable
CREATE TABLE "business_hours" (
    "business_hours_id" UUID NOT NULL,
    "open_week_day" "WeekDay" NOT NULL,
    "open_from_hour" TEXT NOT NULL,
    "open_to_hour" TEXT NOT NULL,
    "business_config_id" UUID NOT NULL,

    CONSTRAINT "business_hours_pkey" PRIMARY KEY ("business_hours_id")
);

-- CreateTable
CREATE TABLE "address" (
    "address_id" UUID NOT NULL,
    "street" TEXT NOT NULL,
    "street_number" TEXT NOT NULL,
    "floor" TEXT,
    "apartment" TEXT,
    "city" TEXT NOT NULL,
    "province" TEXT NOT NULL,
    "postal_code" TEXT,
    "business_config_id" UUID NOT NULL,

    CONSTRAINT "address_pkey" PRIMARY KEY ("address_id")
);

-- CreateTable
CREATE TABLE "client" (
    "client_id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "last_name" TEXT NOT NULL,
    "phone_number" TEXT NOT NULL,

    CONSTRAINT "client_pkey" PRIMARY KEY ("client_id")
);

-- CreateTable
CREATE TABLE "conversation" (
    "conversation_id" UUID NOT NULL,
    "overall_sentiment" TEXT,
    "last_intent" TEXT,
    "channel" TEXT NOT NULL DEFAULT 'WHATSAPP',
    "client_id" UUID,

    CONSTRAINT "conversation_pkey" PRIMARY KEY ("conversation_id")
);

-- CreateTable
CREATE TABLE "message" (
    "message_id" UUID NOT NULL,
    "conversation_id" UUID NOT NULL,
    "role" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "detected_intent" TEXT,
    "sentiment" TEXT,
    "status" TEXT,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "message_pkey" PRIMARY KEY ("message_id")
);

-- CreateTable
CREATE TABLE "order" (
    "order_id" UUID NOT NULL,
    "estimated_time" INTEGER,
    "delivery_type" "DeliveryType",
    "payment_type" "PaymentType",
    "status" "OrderStatus" NOT NULL DEFAULT 'BORRADOR',
    "shipping_cost" DECIMAL(10,2),
    "total_amount" DECIMAL(10,2),
    "client_id" UUID,
    "address_id" UUID,
    "conversation_id" UUID,

    CONSTRAINT "order_pkey" PRIMARY KEY ("order_id")
);

-- CreateTable
CREATE TABLE "order_line" (
    "order_line_id" UUID NOT NULL,
    "order_id" UUID NOT NULL,
    "product_id" UUID NOT NULL,
    "amount" INTEGER NOT NULL,
    "unit_price" DECIMAL(10,2),
    "subtotal" DECIMAL(10,2) NOT NULL,
    "discount_id" UUID,

    CONSTRAINT "order_line_pkey" PRIMARY KEY ("order_line_id")
);

-- CreateTable
CREATE TABLE "product" (
    "product_id" UUID NOT NULL,
    "description" TEXT NOT NULL,
    "available" BOOLEAN NOT NULL DEFAULT true,
    "category_id" UUID NOT NULL,

    CONSTRAINT "product_pkey" PRIMARY KEY ("product_id")
);

-- CreateTable
CREATE TABLE "price" (
    "price_id" UUID NOT NULL,
    "product_id" UUID NOT NULL,
    "since_date" TIMESTAMP(3) NOT NULL,
    "price" DECIMAL(10,2) NOT NULL,

    CONSTRAINT "price_pkey" PRIMARY KEY ("price_id")
);

-- CreateTable
CREATE TABLE "category" (
    "category_id" UUID NOT NULL,
    "description" TEXT NOT NULL,

    CONSTRAINT "category_pkey" PRIMARY KEY ("category_id")
);

-- CreateTable
CREATE TABLE "discount" (
    "discount_id" UUID NOT NULL,
    "percentage" DECIMAL(5,2) NOT NULL,

    CONSTRAINT "discount_pkey" PRIMARY KEY ("discount_id")
);

-- CreateTable
CREATE TABLE "coupon" (
    "coupon_id" UUID NOT NULL,
    "coupon_code" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "amount" DECIMAL(10,2) NOT NULL,
    "available_uses" INTEGER NOT NULL,
    "date_of_expiration" TIMESTAMP(3),

    CONSTRAINT "coupon_pkey" PRIMARY KEY ("coupon_id")
);

-- CreateTable
CREATE TABLE "applied_coupon" (
    "applied_coupon_id" UUID NOT NULL,
    "order_id" UUID NOT NULL,
    "coupon_id" UUID,
    "coupon_code" TEXT NOT NULL,
    "type" TEXT NOT NULL,
    "amount" DECIMAL(10,2) NOT NULL,
    "discount_amount" DECIMAL(10,2) NOT NULL,
    "available_uses" INTEGER NOT NULL,
    "date_of_expiration" TIMESTAMP(3),
    "applied_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "applied_coupon_pkey" PRIMARY KEY ("applied_coupon_id")
);

-- CreateTable
CREATE TABLE "payment" (
    "payment_id" UUID NOT NULL,
    "order_id" UUID NOT NULL,
    "provider" TEXT NOT NULL,
    "external_id" TEXT,
    "status" "PaymentStatus" NOT NULL DEFAULT 'PENDIENTE',
    "amount" DECIMAL(10,2) NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "payment_pkey" PRIMARY KEY ("payment_id")
);

-- CreateIndex
CREATE UNIQUE INDEX "client_phone_number_key" ON "client"("phone_number");

-- CreateIndex
CREATE INDEX "message_conversation_id_idx" ON "message"("conversation_id");

-- CreateIndex
CREATE INDEX "order_client_id_idx" ON "order"("client_id");

-- CreateIndex
CREATE INDEX "order_status_idx" ON "order"("status");

-- CreateIndex
CREATE INDEX "order_conversation_id_idx" ON "order"("conversation_id");

-- CreateIndex
CREATE INDEX "order_line_product_id_idx" ON "order_line"("product_id");

-- CreateIndex
CREATE UNIQUE INDEX "order_line_order_id_product_id_key" ON "order_line"("order_id", "product_id");

-- CreateIndex
CREATE INDEX "product_category_id_idx" ON "product"("category_id");

-- CreateIndex
CREATE INDEX "price_product_id_since_date_idx" ON "price"("product_id", "since_date");

-- CreateIndex
CREATE UNIQUE INDEX "coupon_coupon_code_key" ON "coupon"("coupon_code");

-- CreateIndex
CREATE INDEX "applied_coupon_order_id_idx" ON "applied_coupon"("order_id");

-- CreateIndex
CREATE INDEX "payment_order_id_idx" ON "payment"("order_id");

-- AddForeignKey
ALTER TABLE "business_hours" ADD CONSTRAINT "business_hours_business_config_id_fkey" FOREIGN KEY ("business_config_id") REFERENCES "business_configuration"("business_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "address" ADD CONSTRAINT "address_business_config_id_fkey" FOREIGN KEY ("business_config_id") REFERENCES "business_configuration"("business_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "conversation" ADD CONSTRAINT "conversation_client_id_fkey" FOREIGN KEY ("client_id") REFERENCES "client"("client_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "message" ADD CONSTRAINT "message_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "conversation"("conversation_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order" ADD CONSTRAINT "order_client_id_fkey" FOREIGN KEY ("client_id") REFERENCES "client"("client_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order" ADD CONSTRAINT "order_address_id_fkey" FOREIGN KEY ("address_id") REFERENCES "address"("address_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order" ADD CONSTRAINT "order_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "conversation"("conversation_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_line" ADD CONSTRAINT "order_line_order_id_fkey" FOREIGN KEY ("order_id") REFERENCES "order"("order_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_line" ADD CONSTRAINT "order_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "product"("product_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "order_line" ADD CONSTRAINT "order_line_discount_id_fkey" FOREIGN KEY ("discount_id") REFERENCES "discount"("discount_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "product" ADD CONSTRAINT "product_category_id_fkey" FOREIGN KEY ("category_id") REFERENCES "category"("category_id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "price" ADD CONSTRAINT "price_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "product"("product_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "applied_coupon" ADD CONSTRAINT "applied_coupon_order_id_fkey" FOREIGN KEY ("order_id") REFERENCES "order"("order_id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "applied_coupon" ADD CONSTRAINT "applied_coupon_coupon_id_fkey" FOREIGN KEY ("coupon_id") REFERENCES "coupon"("coupon_id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "payment" ADD CONSTRAINT "payment_order_id_fkey" FOREIGN KEY ("order_id") REFERENCES "order"("order_id") ON DELETE CASCADE ON UPDATE CASCADE;
