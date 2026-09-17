```mermaid
stateDiagram-v2
    [*] --> BORRADOR

    BORRADOR --> PENDIENTE: cliente (agente) confirma
    BORRADOR --> CONFIRMADO: pedido manual (mostrador) aceptado por el negocio
    BORRADOR --> CANCELADO: cliente abandona

    PENDIENTE --> PAGADO: pago ONLINE aprobado
    PENDIENTE --> CONFIRMADO: pago en efectivo y negocio acepta
    PENDIENTE --> BORRADOR: reapertura por modificacion (solo ONLINE sin pago aprobado)
    PENDIENTE --> CANCELADO: cliente o negocio cancela

    PAGADO --> CONFIRMADO: negocio acepta el pedido pagado
    CONFIRMADO --> EN_PREPARACION: negocio inicia preparacion
    PAGADO --> CANCELADO: solo antes de preparar
    CONFIRMADO --> CANCELADO: solo antes de preparar

    EN_PREPARACION --> LISTO: finaliza preparacion

    LISTO --> ENTREGADO: tipo de entrega ENVIO
    LISTO --> RETIRADO: tipo de entrega RETIRO
```

## Reglas implementadas

- **`PAGADO` (PAID)** solo lo produce un pago online **verificado por el proveedor** (webhook de Mercado Pago). Un pedido manual **nunca** pasa por `PAGADO` aunque se cobre: el pedido manual nace aceptado por el operador y va directo a `CONFIRMADO`.
- **Origen**: `IN_PLACE` (mostrador/POS) confirma a `CONFIRMADO`; `AGENT` (WhatsApp/IA) confirma a `PENDIENTE` y espera la liquidacion (pago online -> `PAGADO`, efectivo aceptado -> `CONFIRMADO`).
- **`PENDIENTE -> PAGADO`** solo si `paymentType = ONLINE`; **`PENDIENTE -> CONFIRMADO`** solo si `paymentType = CASH`. Si el metodo no esta especificado (pedidos manuales viejos), ambas transiciones quedan disponibles para el operador.
- **Reapertura**: `PENDIENTE -> BORRADOR` solo para pedidos `ONLINE` sin un intento de pago aprobado de la version actual. Modificar invalida la confirmacion (`confirmedAt` se limpia) y supersede el checkout anterior; hay que volver a confirmar.
- **Cancelacion**: permitida solo desde `BORRADOR`, `PENDIENTE`, `PAGADO` o `CONFIRMADO` (nunca desde `EN_PREPARACION` o posterior).
- Un pedido con pago aprobado de la version actual queda inmutable: un nuevo producto implica un pedido nuevo.
