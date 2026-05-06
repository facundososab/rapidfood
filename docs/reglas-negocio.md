# Reglas de negocio

## Ciclo de vida del pedido

- RN-001: Un pedido inicia en estado BORRADOR cuando el agente comienza a construirlo
- RN-002: Un pedido en BORRADOR puede modificarse libremente (agregar o quitar productos)
- RN-003: Un pedido pasa de BORRADOR a PENDIENTE cuando el cliente confirma explicitamente
- RN-004: Al pasar a PENDIENTE se valida: monto minimo, productos disponibles, direccion en zona de cobertura (si es ENVIO), horario de atencion, metodo de pago seleccionado
- RN-005: Un pedido en BORRADOR puede abandonarse y debe limpiarse despues de 24 horas sin actividad
- RN-006: Un pedido solo puede modificarse si su estado es BORRADOR
- RN-007: Un pedido puede cancelarse si su estado es PENDIENTE, CONFIRMADO o PAGADO (no si ya esta EN_PREPARACION o posterior)
- RN-008: BORRADOR -> PENDIENTE cuando el cliente confirma
- RN-009: BORRADOR -> CANCELADO cuando el cliente abandona explicitamente
- RN-010: PENDIENTE -> PAGADO cuando el pago online es aprobado
- RN-011: PENDIENTE -> CONFIRMADO cuando el pago es en efectivo y el negocio acepta
- RN-012: PENDIENTE -> CANCELADO cuando el cliente o el negocio cancela
- RN-013: CONFIRMADO -> EN_PREPARACION cuando el negocio inicia la preparacion
- RN-014: PAGADO -> EN_PREPARACION cuando el negocio inicia la preparacion
- RN-015: EN_PREPARACION -> LISTO cuando finaliza la preparacion
- RN-016: LISTO -> ENTREGADO si el tipo de entrega es ENVIO
- RN-017: LISTO -> RETIRADO si el tipo de entrega es RETIRO
- RN-018: CONFIRMADO -> CANCELADO solo antes de preparar
- RN-019: PAGADO -> CANCELADO solo antes de preparar

## Validaciones especificas por estado

- RN-020: En estado BORRADOR no se requiere direccion completa
- RN-021: En estado BORRADOR no se requiere metodo de pago
- RN-022: En estado BORRADOR no se valida monto minimo ni horarios
- RN-023: Al pasar de BORRADOR a PENDIENTE se valida todo (direccion, pago, monto, horario, disponibilidad)
- RN-024: Al pasar de BORRADOR a PENDIENTE se registra el precio actual de cada producto en la linea del pedido
- RN-025: Al pasar de BORRADOR a PENDIENTE se calcula el tiempo estimado
- RN-026: En PENDIENTE o posterior los precios de las lineas son inmutables y no se pueden agregar o quitar productos
- RN-027: Cambios posteriores en el precio de un producto no afectan al pedido

## Conversacion y pedido

- RN-028: Cada conversacion puede tener un solo pedido en BORRADOR activo
- RN-029: Si el cliente inicia un nuevo pedido mientras hay uno en BORRADOR, el sistema pregunta si desea continuar o empezar uno nuevo
- RN-030: Un pedido en BORRADOR debe tener referencia a la conversacion que lo esta construyendo
- RN-031: Una conversacion puede tener multiples pedidos en estado PENDIENTE o posterior

## Reglas de calculo

- RN-032: Durante BORRADOR, el subtotal del pedido es la suma de los importes de sus lineas y se recalcula al agregar o quitar productos
- RN-033: Durante BORRADOR, el descuento del pedido es la suma de los descuentos aplicados por cupones
- RN-034: Durante BORRADOR, el total del pedido es subtotal menos descuento mas costo de envio
- RN-035: Al confirmar (BORRADOR -> PENDIENTE), cada linea registra el precio vigente del producto y su importe
- RN-036: El costo de envio es 0 si el tipo de entrega es RETIRO; si es ENVIO, es 0 cuando el subtotal supera el umbral de envio gratis, si no se aplica el costo de envio definido por el negocio
- RN-037: El tiempo estimado es el tiempo de preparacion mas el tiempo de envio cuando corresponde

## Pagos

- RN-038: Cada intento de pago online crea un pago en estado pendiente y se asocia al pedido
- RN-039: Si el estado del pago cambia a aprobado y el pedido esta en PENDIENTE, el pedido pasa a PAGADO
- RN-040: Si el estado del pago cambia a rechazado, fallido o vencido, el pedido permanece en PENDIENTE
- RN-041: Si el metodo de pago es en efectivo, el pedido pasa a CONFIRMADO cuando el negocio acepta el pedido
