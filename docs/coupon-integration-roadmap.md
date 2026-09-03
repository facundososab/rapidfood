# Roadmap de integración — Módulo `config_coupon`

> Estado: el módulo está implementado como **panel de administración** (REST). La
> integración con el módulo `order` y el modelo definitivo de usos de cupones
> quedan pendientes y se describen acá.

## 1. Estado actual (hecho)

- Panel admin REST: crear, listar, consultar por código, activar/pausar.
- Dominio + use cases con invariantes RN-01..RN-09 y unit tests sin BD.
- Enrutado en `api/coupons/`.
- `validate`/`consume` quedaron **internos** (no expuestos por HTTP), disponibles
  vía los puertos `ValidateCouponPort` / `ConsumeCouponPort` para consumo in-process.

## 2. Decisiones pendientes

### 2.1 Modelo de usos (por persona vs global)

- Hoy el dominio usa `available_uses` como contador **global** (RN-06).
- El negocio se inclina a **usos por persona** (por cliente).
- Implicancias si es por persona:
  - Reemplazar el contador global por usos trackeados por cliente.
  - Derivar los usos de `AppliedCoupon` + `Order.clientId`, o agregar una tabla
    de usos por cliente.
  - Cambiar dominio (`consume_use`), schema (`Coupon.availableUses`) y el contrato
    `ConsumeCouponCommand` (que hoy solo recibe `coupon_code`).

### 2.2 Consumo atómico

- Recién cuando el modelo de usos esté cerrado. Hoy el consumo es read-modify-write
  no atómico (race condition). Opciones: decremento condicional Prisma o transacción.

## 3. Contratos cross-module (order ↔ config_coupon)

- Borde oficial: `ValidateCouponPort.execute(ValidateCouponCommand) -> ValidateCouponResponse`
  y `ConsumeCouponPort.execute(ConsumeCouponCommand) -> ConsumeCouponResponse`.
- `order` hoy define su propio `CouponQueryPort` (firma distinta) y usa `FakeCouponQuery`
  (descuento fijo 50.00). Falta un adapter que una ambos y reemplace el fake.
- Traducción de errores: `DomainError` → "cupón inválido" del lado de `order`.

## 4. Snapshot `AppliedCoupon`

- El modelo `AppliedCoupon` (schema) es un snapshot congelado del cupón aplicado.
- Hoy **nadie lo persiste**. Hay que definir quién lo escribe (probablemente `order`
  al aplicar/confirmar) y si `ConsumeCouponCommand` debe recibir `order_id`.

## 5. Consumo en la transición

- RN-07: el consumo ocurre en BORRADOR → PENDIENTE, no al aplicar el cupón al borrador.
- `order` debe invocar `ConsumeCouponPort` en el confirm, no en el apply.

## 6. Pasos sugeridos de continuación

1. Cerrar la decisión del modelo de usos (2.1).
2. Ajustar dominio + schema + contrato de consumo según esa decisión.
3. Escribir el adapter `order → config_coupon` y reemplazar `FakeCouponQuery`.
4. Definir y persistir el snapshot `AppliedCoupon`.
5. Implementar consumo atómico.
6. Tests de integración (requiere Postgres/Docker).
