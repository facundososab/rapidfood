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

## 2. Decisiones

### 2.1 Modelo de usos — RESUELTO

- `available_uses` es **opcional**: `None` = cupón ilimitado (cada cliente puede
  usarlo sin límite), `N` = contador global que se descuenta y agota en 0.
- **Sin** límite por cliente (cupón no nominal): se descartó la tabla de usos por
  cliente por complejidad innecesaria.

### 2.2 Consumo atómico — pendiente

- El consumo (`consume_use`) sigue siendo read-modify-write no atómico. Recién
  aplica cuando `order` consuma cupones en BORRADOR→PENDIENTE. Opciones:
  decremento condicional Prisma o transacción.

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

1. ~~Cerrar la decisión del modelo de usos (2.1)~~ ✅ hecho.
2. ~~Ajustar dominio + schema + contrato de consumo~~ ✅ hecho.
3. Escribir el adapter `order → config_coupon` y reemplazar `FakeCouponQuery`.
4. Definir y persistir el snapshot `AppliedCoupon`.
5. Implementar consumo atómico.
6. Tests de integración (requiere Postgres/Docker).
