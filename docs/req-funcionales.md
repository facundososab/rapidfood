# Requerimientos funcionales

## Administracion del negocio

- REQ-001: El sistema debe permitir al administrador crear, editar y desactivar productos
- REQ-002: El sistema debe permitir gestionar categorias de productos
- REQ-003: El sistema debe permitir cargar y actualizar precios, registrando la vigencia de cada precio
- REQ-004: El sistema debe permitir marcar la disponibilidad de productos
- REQ-005: El sistema debe permitir gestionar cupones y promociones (tipo, monto, usos disponibles y vencimiento)
- REQ-006: El sistema debe permitir crear cupones de un solo uso o de usos multiples
- REQ-007: El sistema debe permitir asociar un cupon a un pedido especifico cuando se requiera
- REQ-008: El sistema debe permitir definir la informacion del negocio (nombre, direccion y zona de cobertura)
- REQ-009: El sistema debe permitir definir horarios de atencion por dia
- REQ-010: El sistema debe permitir configurar monto minimo y costo de envio
- REQ-011: El sistema debe permitir consultar pedidos por estado y fecha
- REQ-012: El sistema debe permitir actualizar el estado del pedido segun el flujo operativo
- REQ-013: El sistema debe permitir ver el detalle del pedido (productos, totales, cliente, direccion y pagos)
- REQ-014: El sistema debe permitir ver el estado de los pagos asociados a un pedido

## Gestion del pedido

- REQ-015: El sistema debe crear automaticamente un pedido en estado BORRADOR cuando el agente detecta intencion de hacer un pedido
- REQ-016: El sistema debe permitir agregar productos a un pedido en estado BORRADOR
- REQ-017: El sistema debe permitir modificar cantidades en un pedido en estado BORRADOR
- REQ-018: El sistema debe permitir eliminar productos de un pedido en estado BORRADOR
- REQ-019: El sistema debe recalcular subtotal y total automaticamente al modificar el pedido en BORRADOR
- REQ-020: El sistema debe permitir aplicar o quitar cupones en estado BORRADOR
- REQ-021: El sistema debe validar todas las reglas de negocio al intentar confirmar (BORRADOR -> PENDIENTE)
- REQ-022: El sistema debe impedir confirmar si faltan datos obligatorios (direccion si ENVIO, metodo de pago, etc.)
- REQ-023: El sistema debe congelar precios al confirmar (registrar precio vigente del producto)
- REQ-024: El sistema debe permitir cancelar un pedido en BORRADOR (cliente abandona el carrito)
- REQ-025: El sistema debe limpiar automaticamente pedidos en BORRADOR con mas de 24 horas sin actividad
- REQ-026: El sistema debe mostrar al cliente el resumen del pedido antes de confirmar (productos, totales, direccion, tiempo estimado)

## Agente conversacional

- REQ-027: El agente debe detectar cuando un cliente quiere empezar un pedido nuevo
- REQ-028: El agente debe verificar si ya existe un pedido en BORRADOR para esa conversacion
- REQ-029: Si existe un pedido en BORRADOR anterior, el agente debe preguntar si desea continuar o empezar uno nuevo
- REQ-030: El agente debe ir construyendo el pedido en BORRADOR conforme el cliente menciona productos
- REQ-031: El agente debe actualizar el pedido en BORRADOR cuando el cliente modifica cantidades o productos
- REQ-032: El agente debe mostrar el estado actual del pedido cuando el cliente lo solicita
- REQ-033: El agente debe solicitar datos faltantes antes de confirmar: tipo de entrega, direccion (si ENVIO) y metodo de pago
- REQ-034: El agente debe validar en tiempo real disponibilidad de productos, zona de cobertura y horario de atencion antes de confirmar
- REQ-035: El agente debe mostrar el total actualizado despues de cada modificacion
- REQ-036: El agente debe confirmar explicitamente con el cliente antes de pasar a PENDIENTE
- REQ-037: El agente debe informar el tiempo estimado de entrega o preparacion al confirmar

## Consulta de estado

- REQ-038: El sistema debe permitir consultar el pedido actual en BORRADOR de una conversacion
- REQ-039: El sistema debe permitir consultar pedidos confirmados (PENDIENTE o posterior) de un cliente
- REQ-040: El agente debe poder informar el estado de un pedido especifico cuando el cliente lo consulta
- REQ-041: El agente debe poder listar los ultimos pedidos del cliente

## Transiciones de estado

- REQ-042: El sistema debe permitir que el negocio acepte un pedido en PENDIENTE cuando el metodo de pago es en efectivo (PENDIENTE -> CONFIRMADO)
- REQ-043: El sistema debe permitir que el negocio cancele un pedido en PENDIENTE o CONFIRMADO antes de preparar
- REQ-044: El sistema debe permitir avanzar el estado: CONFIRMADO o PAGADO -> EN_PREPARACION -> LISTO -> ENTREGADO o RETIRADO
- REQ-045: El sistema debe notificar al cliente cuando cambia el estado de su pedido
- REQ-046: El sistema debe validar transiciones de estado permitidas

## Pagos

- REQ-047: El sistema debe generar un enlace de pago cuando el metodo de pago es online y el pedido esta en PENDIENTE
- REQ-048: El sistema debe registrar un pago en estado pendiente al crear el enlace de pago
- REQ-049: El sistema debe recibir notificaciones del proveedor y actualizar el estado del pago (aprobado, rechazado, fallido, vencido)
- REQ-050: Si el pago pasa a aprobado, el sistema debe actualizar el estado del pedido a PAGADO
- REQ-051: Si el pago pasa a rechazado, fallido o vencido, el pedido debe permanecer en PENDIENTE y el agente debe ofrecer reintentar el pago

## Recuperacion de pedidos

- REQ-052: Si un cliente vuelve despues de abandonar la conversacion, el agente debe poder recuperar el pedido en BORRADOR (si no expiro)
- REQ-053: El agente debe preguntar si desea continuar con el pedido anterior o empezar uno nuevo
