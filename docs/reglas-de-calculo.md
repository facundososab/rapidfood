# Reglas de cálculo

Este documento describe, de forma **exacta y trazable al código**, cómo Rapidfood
calcula tres cosas:

1. el **precio total** de un pedido,
2. el **costo de envío**, y
3. el **tiempo de entrega estimado (ETA)**.

Todas las fórmulas están implementadas en el dominio (funciones puras, sin
dependencias externas) y los valores monetarios se calculan con `Decimal` y se
redondean a 2 decimales con `ROUND_HALF_UP` (nunca con `float`).

---

## 1. Precio de cada línea

Cada línea del pedido se valida contra el catálogo y se calcula así:

```
precio_unitario_línea = precio_actual_de_la_variante + Σ price_delta_de_modificadores
subtotal_línea        = precio_unitario_línea × cantidad
```

- `precio_actual_de_la_variante`: precio vigente de la variante elegida
  (Simple / Doble / Triple, etc.).
- `price_delta_de_modificadores`: suma de los adicionales de los modificadores
  seleccionados (extras).
- Quitar ingredientes **no** cambia el precio.

> Implementación: `api/modules/order/application/use_cases/add_item_to_order_use_case.py`
> (líneas del cálculo de `unit_price` y `subtotal`).

---

## 2. Subtotal del pedido

```
subtotal = Σ subtotal_línea
```

> Implementación: `Order._recalculate_totals()`
> (`api/modules/order/domain/models/order.py`).

---

## 3. Descuento (cupones)

El descuento lo calcula el módulo de cupones contra el **subtotal** (nunca contra
el total ni el envío). Hay dos tipos:

| Tipo | Fórmula | Regla adicional |
|------|---------|-----------------|
| `FIXED_AMOUNT` | `descuento = min(monto, subtotal)` | Requiere un **pedido mínimo**; nunca descuenta más que el subtotal |
| `PERCENTAGE` | `descuento = subtotal × porcentaje / 100` | Sin tope |

El resultado se redondea a 2 decimales (`ROUND_HALF_UP`). Un pedido admite **un
solo cupón**, y el descuento se congela en el pedido al aplicarlo.

> Implementación: `Coupon.calculate_discount()`
> (`api/modules/config_coupon/domain/models/coupon.py`).

---

## 4. Costo de envío

El envío se cotiza en tiempo real (geocodificación + ruteo) y luego se ajusta por
**día de la semana** y por **demanda**:

```
recargo_distancia = distancia_km × precio_por_km
base              = costo_base_envío + recargo_distancia
costo_envío       = base × multiplicador_día × multiplicador_demanda
```

Luego se redondea a 2 decimales (`ROUND_HALF_UP`).

### 4.1 Distancia

- Se **geocodifica** la dirección del cliente y la del local (origen).
- Se calcula la **ruta en auto** con OpenRouteService (`profile="driving-car"`),
  que devuelve la distancia en metros y la duración en segundos.

### 4.2 Multiplicador por día de la semana

Cada día tiene su multiplicador configurable (por defecto `1,00`).

### 4.3 Multiplicador por demanda

Se cuentan las órdenes activas **de delivery** (`CONFIRMED` + `IN_PREPARATION`) y
se clasifica la demanda con los **umbrales de envío**:

| Demanda | Condición | Multiplicador |
|---------|-----------|---------------|
| `NORMAL` | `activas < umbral_alto` | `1,00` (fijo) |
| `HIGH` | `umbral_alto ≤ activas < umbral_muy_alto` | `multiplicador_demanda_alta` (config) |
| `VERY_HIGH` | `activas ≥ umbral_muy_alto` | `multiplicador_demanda_muy_alta` (config) |

Si la dirección está **fuera de la zona de reparto**, el envío se considera no
disponible (no se cobra ni se permite confirmar con envío).

> Implementación:
> `api/modules/delivery/domain/services/delivery_price_calculator.py` (fórmula),
> `api/modules/delivery/domain/services/demand_classifier.py` (clasificación),
> `api/modules/delivery/application/use_cases/calculate_delivery_quote_use_case.py`
> (geocodificación + ruteo + armado del quote).

---

## 5. Precio total del pedido

```
total = max( subtotal − descuento + costo_envío , 0 )
```

El total nunca puede ser negativo. El envío se suma **después** del descuento (el
cupón aplica solo al subtotal).

> Implementación: `Order._recalculate_totals()`
> (`api/modules/order/domain/models/order.py`).

---

## 6. Tiempo de entrega estimado (ETA)

El ETA se compone de tres partes:

```
tiempo_preparación = minutos_por_demanda + margen_fijo
ETA                = tiempo_preparación + duración_del_viaje   (envío a domicilio)
ETA                = tiempo_preparación                        (retiro en el local)
```

### 6.1 Preparación por demanda (umbrales propios, independientes de envío)

Se cuentan **todas** las órdenes activas (`CONFIRMED` + `IN_PREPARATION`), sin
importar si son envío o retiro (ambas cargan la cocina), y se clasifica con los
**umbrales propios del tiempo de preparación**:

| Demanda | Condición | Minutos base |
|---------|-----------|--------------|
| `NORMAL` | `activas < umbral_alto` | `minutos_normal` |
| `HIGH` | `umbral_alto ≤ activas < umbral_muy_alto` | `minutos_demanda_alta` |
| `VERY_HIGH` | `activas ≥ umbral_muy_alto` | `minutos_demanda_muy_alta` |

### 6.2 Margen fijo

`margen_fijo` cubre espera del repartidor y repartos agrupados (varias entregas en
un mismo viaje), que el ruteo directo no contempla.

### 6.3 Duración del viaje

Es la duración de la ruta en auto local → cliente que devuelve OpenRouteService,
convertida de segundos a minutos. **No** incluye tráfico en vivo.

### 6.4 Cuándo se calcula y se recalcula

- Al **configurar la entrega o el retiro** se guarda un ETA **provisorio**
  (y se persiste la duración del viaje).
- Al **confirmar** el pedido se **recalcula** el ETA con la demanda del momento,
  reutilizando la duración del viaje ya guardada (no se repite el ruteo).
- Si no hay configuración cargada, se usan valores por defecto
  (`umbrales 8/15`, `minutos 20/35/50`, `margen 5`).

> Implementación:
> `api/modules/order/domain/services/prep_time_classifier.py` (clasificación),
> `api/modules/order/infrastructure/adapters/driven/prisma/preparation_time_estimator.py`
> (config + conteo + clasificación), y los use cases de entrega/retiro/confirmación
> en `api/modules/order/application/use_cases/`.

---

## 7. Ejemplo numérico completo

**Pedido:** 1× Bacon BBQ Doble ($10.200) + 1× Coca-Cola Zero 500 ml ($2.200),
envío a 4 km del local.

| Concepto | Cálculo | Valor |
|----------|---------|-------|
| Subtotal | 10.200 + 2.200 | **$12.400** |
| Descuento | sin cupón | **$0** |
| Recargo por distancia | 4 km × $250/km | $1.000 |
| Base de envío | $1.000 (base) + $1.000 | $2.000 |
| Multiplicador día | viernes ×1,00 | $2.000 |
| Costo de envío | $2.000 × 1,00 × 1,00 | **$2.000** |
| **Total** | 12.400 − 0 + 2.000 | **$14.400** |

**ETA:** demanda `NORMAL` → 20 min de preparación + 5 min de margen = 25 min;
viaje 12 min → **37 min**.

Si la demanda sube a `HIGH` (p. ej. 10 órdenes activas y umbral alto = 8):
preparación = 35 + 5 = 40 min → **ETA = 52 min** (el envío también subiría si el
multiplicador de demanda de envío es > 1,00).

---

## 8. Dónde se configura cada parámetro

| Parámetro | Dónde | Tabla / campo |
|-----------|-------|---------------|
| Precios de variantes y modificadores | Catálogo (panel) | `price`, `modifier_option.price_delta` |
| Cupones (tipo, monto, mínimo, usos, vencimiento) | Cupones (panel) | `coupon` |
| `costo_base_envío`, `precio_por_km`, umbrales y multiplicadores de demanda de envío, multiplicadores por día | Configuración → **Envíos y demanda** | `delivery_pricing_configuration`, `delivery_weekday_pricing_rule` |
| Umbrales y minutos de preparación + margen | Configuración → **Tiempos de preparación** | `preparation_time_configuration` |

---

## 9. Resumen de fórmulas

```
subtotal_línea = (precio_variante + Σ extras) × cantidad
subtotal       = Σ subtotal_línea
descuento      = cupón (fijo: min(monto, subtotal) | porcentaje: subtotal × %/100)
costo_envío    = (base + distancia_km × precio_km) × mult_día × mult_demanda
total          = max(subtotal − descuento + costo_envío, 0)

preparación    = minutos_por_demanda + margen
ETA            = preparación + duración_viaje   (delivery)
ETA            = preparación                    (pickup)
```

Todo cálculo monetario se redondea a 2 decimales con `ROUND_HALF_UP`.
