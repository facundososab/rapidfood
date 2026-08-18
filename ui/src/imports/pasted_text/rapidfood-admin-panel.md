Quiero que diseñes e implementes el **panel administrativo de Rapidfood**, un SaaS para restaurantes que reciben y gestionan pedidos de comida.

Rapidfood utiliza un agente conversacional conectado al sistema para gestionar conversaciones con clientes y generar pedidos. Sin embargo, el personal del restaurante también debe poder **crear pedidos manualmente desde el panel administrativo**.

Te proporciono el `schema.prisma` del proyecto.

## REGLA PRINCIPAL

El `schema.prisma` es la **única fuente de verdad para los datos disponibles**.

No inventes campos, entidades, relaciones, estados ni funcionalidades que no puedan representarse con este modelo.

Puedes calcular información derivada utilizando las relaciones existentes, pero debes diferenciar claramente:

* campos persistidos;
* valores calculados;
* estados visuales derivados.

No agregues datos ficticios al modelo solamente porque sean habituales en otros sistemas de delivery.

Por ejemplo, actualmente NO existen en el modelo:

* imágenes de productos;
* variantes;
* modificadores;
* adicionales;
* stock;
* SKU;
* email del cliente;
* fecha de nacimiento;
* dirección perteneciente directamente al cliente;
* repartidores;
* tracking del delivery;
* historial de estados del pedido;
* `updatedAt` del pedido;
* origen del pedido (`MANUAL`, `AI`, etc.);
* estado de intervención humana en conversaciones;
* mensajes no leídos;
* roles y permisos;
* métodos de pago distintos de `CASH` y `ONLINE`;
* fecha de inicio de cupones;
* mínimo de compra de cupones;
* restricciones de cupones por producto o cliente;
* estado `active` de un cupón;
* sucursales como entidad independiente.

No diseñes funcionalidades basadas en esos datos.

---

# MODELO DE DATOS EXISTENTE

Las entidades relevantes son:

* `BusinessConfiguration`
* `BusinessHours`
* `Address`
* `Client`
* `Conversation`
* `Message`
* `Order`
* `OrderLine`
* `Product`
* `Price`
* `Category`
* `Discount`
* `Coupon`
* `AppliedCoupon`
* `Payment`

Estados de pedido disponibles:

* `DRAFT`
* `PENDING`
* `PAID`
* `CONFIRMED`
* `IN_PREPARATION`
* `READY`
* `DELIVERED`
* `PICKED_UP`
* `CANCELLED`

Tipos de entrega:

* `DELIVERY`
* `PICKUP`

Tipos de pago del pedido:

* `CASH`
* `ONLINE`

Estados de pagos:

* `PENDING`
* `APPROVED`
* `REJECTED`
* `FAILED`
* `EXPIRED`

---

# ESTRUCTURA DEL PANEL

La navegación principal debe contener:

1. Dashboard
2. Pedidos
3. Productos
4. Pagos
5. Clientes
6. Cupones
7. Conversaciones

Agregar además una sección secundaria:

8. Configuración

No agregar otras secciones principales sin una justificación derivada directamente del schema.

---

# 1. DASHBOARD

El Dashboard debe permitir al restaurante entender rápidamente qué está sucediendo en el negocio.

No quiero un dashboard decorativo lleno de gráficos. Cada componente debe responder una pregunta operativa concreta.

## Métricas principales

Mostrar:

### Ventas

Utilizar los datos existentes de `Order` y `Payment`.

Distinguir conceptualmente:

**Facturación de pedidos**
basada en `Order.totalAmount`.

**Dinero efectivamente cobrado online**
basado en `Payment.amount` donde:

`Payment.status = APPROVED`

No mezclar ambas métricas como si fueran lo mismo.

### Pedidos de hoy

Cantidad de `Order` cuyo `createdAt` pertenece al día actual.

### Ticket promedio

Calcular utilizando pedidos válidos cuyo `totalAmount` no sea null.

No incluir `DRAFT` ni `CANCELLED`.

### Pedidos activos

Mostrar cantidad de pedidos en estados operativos:

* `PENDING`
* `PAID`
* `CONFIRMED`
* `IN_PREPARATION`
* `READY`

### Pedidos completados

Diferenciar:

* `DELIVERED`
* `PICKED_UP`

### Cancelados

Cantidad de pedidos `CANCELLED`.

## Selector temporal

Permitir:

* Hoy
* Últimos 7 días
* Últimos 30 días
* rango personalizado

Utilizar `Order.createdAt`, `Order.confirmedAt` y `Payment.createdAt` dependiendo de la métrica correspondiente.

---

# Flujo de pedidos

Crear una visualización compacta mostrando cuántos pedidos existen actualmente en:

DRAFT → PENDING → PAID → CONFIRMED → IN_PREPARATION → READY → DELIVERED / PICKED_UP

Mostrar `CANCELLED` separado del flujo principal.

No asumir que todos los pedidos necesariamente recorren cada estado.

---

# Ventas en el tiempo

Crear un gráfico que permita visualizar:

* monto total de pedidos;
* cantidad de pedidos;

agrupados por día.

Para vista "Hoy", puede agruparse por hora si hay suficiente información.

---

# Productos más vendidos

Calcular utilizando:

`OrderLine.quantity`

relacionado con:

`Product`

Mostrar:

* descripción del producto;
* categoría;
* unidades vendidas;
* facturación generada a partir de los subtotales de líneas.

IMPORTANTE:

`Product` no tiene un campo `name`.

Por lo tanto, utilizar `Product.description` como identificador textual visible del producto.

No inventar un atributo `name`.

---

# Pedidos recientes

Mostrar:

* ID abreviado;
* cliente;
* fecha/hora;
* tipo de entrega;
* tipo de pago;
* total;
* estado.

Cliente:

`Client.name + Client.lastName`

Si `clientId` es null, mostrar algo como:

"Cliente no identificado"

sin inventar información.

---

# Requiere atención

Crear una sección operativa destacada.

Puede incluir únicamente situaciones detectables con el modelo actual:

* pedidos `PENDING`;
* pedidos `PAID`;
* pedidos `CONFIRMED`;
* pedidos `IN_PREPARATION`;
* pedidos `READY`;
* pagos `PENDING`;
* pagos `REJECTED`;
* pagos `FAILED`;
* pagos `EXPIRED`.

Cada elemento debe permitir navegar directamente al pedido o pago correspondiente.

No inventar conceptos como:

* pedido demorado automáticamente;
* repartidor demorado;
* conversación sin responder;
* mensaje no leído;

porque el modelo actual no contiene suficiente información para determinarlo de manera fiable.

---

# 2. PEDIDOS

Esta debe ser una de las secciones centrales del sistema.

Debe estar optimizada para el trabajo cotidiano del restaurante.

## Listado principal

Mostrar una tabla con:

* ID abreviado del pedido;
* cliente;
* fecha;
* tipo de entrega;
* tipo de pago;
* cantidad total de unidades;
* subtotal;
* descuento;
* costo de envío;
* total;
* estado.

La cantidad de unidades debe calcularse como:

sum(`OrderLine.quantity`)

## Filtros

Agregar filtros por:

* estado;
* tipo de entrega;
* tipo de pago;
* fecha;
* cliente.

Permitir búsqueda por:

* ID del pedido;
* nombre del cliente;
* apellido;
* teléfono.

No agregar filtros por datos inexistentes.

---

# Estados del pedido

Utilizar exactamente los valores de `OrderStatus`.

Asignar un badge visual diferente a:

* DRAFT
* PENDING
* PAID
* CONFIRMED
* IN_PREPARATION
* READY
* DELIVERED
* PICKED_UP
* CANCELLED

Los textos visibles pueden traducirse:

DRAFT → Borrador
PENDING → Pendiente
PAID → Pagado
CONFIRMED → Confirmado
IN_PREPARATION → En preparación
READY → Listo
DELIVERED → Entregado
PICKED_UP → Retirado
CANCELLED → Cancelado

Pero los valores internos deben respetar el enum.

---

# Detalle del pedido

Al abrir un pedido crear una página completa.

## Encabezado

Mostrar:

* ID abreviado;
* estado;
* fecha de creación;
* fecha de confirmación si existe;
* tiempo estimado (`estimatedTime`) si existe;
* tipo de entrega;
* tipo de pago.

## Cliente

Si existe:

* nombre;
* apellido;
* teléfono.

Permitir navegar al perfil del cliente.

## Productos

Mostrar cada `OrderLine` con:

* descripción del producto;
* categoría;
* cantidad;
* precio unitario;
* descuento de línea si existe;
* subtotal.

`unitPrice` puede ser null mientras el pedido está en `DRAFT`.

La UI debe manejar explícitamente ese caso.

No mostrar variantes, adicionales o modificadores porque no existen.

## Resumen económico

Mostrar:

Subtotal
Descuento
Costo de envío
Total

Usando:

* `subtotal`
* `discount`
* `shippingCost`
* `totalAmount`

Los valores null deben manejarse correctamente durante estados incompletos.

---

# Cupón aplicado

Utilizar `AppliedCoupon` para mostrar el snapshot real aplicado al pedido.

Mostrar:

* código;
* tipo;
* monto;
* descuento generado;
* fecha de aplicación.

No depender exclusivamente del `Coupon` actual porque `AppliedCoupon` existe precisamente para conservar el snapshot aunque posteriormente cambie o desaparezca el cupón.

---

# Pagos asociados

Un pedido puede tener múltiples registros `Payment`.

Mostrar:

* proveedor;
* monto;
* estado;
* referencia externa si existe;
* fecha de creación;
* última actualización.

Permitir navegar al detalle del pago.

---

# Conversación asociada

Si existe `conversationId`, mostrar una tarjeta:

"Conversación relacionada"

con:

* cliente;
* canal;
* sentimiento general si existe;
* última intención si existe.

Permitir abrir directamente la conversación.

Si `conversationId` es null, no mostrar esta sección.

---

# Dirección

El pedido tiene un `addressId` opcional.

Mostrar la dirección relacionada solamente utilizando los datos existentes:

* street;
* streetNumber;
* floor;
* apartment;
* city;
* province;
* postalCode.

No inventar campos adicionales.

---

# NO CREAR TIMELINE FICTICIA

El modelo NO contiene historial de cambios de estado.

Por lo tanto, no crear una timeline falsa con:

"Pedido creado → confirmado → preparado → enviado → entregado"

Solo existen fechas explícitas para:

* `createdAt`
* `confirmedAt`

Mostrar solamente eventos que realmente puedan reconstruirse con datos existentes.

---

# CREACIÓN MANUAL DE PEDIDOS

Debe existir una acción principal visible:

**+ Nuevo pedido**

El flujo debe parecer un pequeño sistema POS y no un CRUD técnico.

La creación manual debe utilizar exactamente el mismo modelo `Order`.

IMPORTANTE:

El modelo actual NO contiene un campo que permita guardar si un pedido fue creado:

* manualmente;
* por el agente;
* por WhatsApp;
* desde el panel.

Por lo tanto:

NO mostrar ni persistir "Origen: Manual" si el backend no cuenta con ese atributo.

El usuario puede crear manualmente el pedido, pero posteriormente el modelo actual no permite distinguir su origen de manera explícita.

---

# Flujo del pedido manual

## Paso 1 — Cliente

Permitir buscar clientes existentes utilizando:

* nombre;
* apellido;
* teléfono.

Permitir seleccionar uno.

También permitir crear un nuevo cliente solicitando solamente:

* nombre;
* apellido;
* teléfono.

No pedir:

* email;
* documento;
* fecha de nacimiento;

porque no existen.

---

# Paso 2 — Productos

Crear un buscador de productos disponibles.

Mostrar:

* descripción;
* categoría;
* precio actual;
* disponibilidad.

Solo permitir agregar normalmente productos con:

`available = true`

El precio actual debe calcularse a partir de `Price` tomando el registro con:

`max(sinceDate) <= now`

No existe un campo `currentPrice`.

No inventarlo.

Permitir:

* agregar producto;
* aumentar cantidad;
* reducir cantidad;
* eliminar línea.

Como existe:

`@@unique([orderId, productId])`

un mismo producto no debe aparecer como múltiples líneas independientes.

Debe aumentar `quantity` de la línea existente.

---

# Paso 3 — Entrega

Permitir seleccionar:

* DELIVERY
* PICKUP

Utilizar `Order.deliveryType`.

Mostrar el costo de envío utilizando `BusinessConfiguration.shippingCost` cuando corresponda y de acuerdo con la lógica del backend.

Mostrar también:

`BusinessConfiguration.minOrder`

y validar el mínimo del pedido cuando corresponda.

No inventar reglas adicionales.

---

# Paso 4 — Cupón

Permitir introducir un `couponCode`.

Validar utilizando:

* `availableUses`;
* `dateOfExpiration`;
* `type`;
* `amount`.

No agregar:

* fecha de inicio;
* mínimo de compra;
* límite por cliente;
* productos incluidos;
* categorías incluidas;

porque no existen.

Mostrar el descuento calculado antes de confirmar el pedido.

---

# Paso 5 — Pago

Permitir seleccionar únicamente:

* Efectivo (`CASH`)
* Online (`ONLINE`)

Esto corresponde a `Order.paymentType`.

No confundir `PaymentType` con `Payment.provider`.

Cuando el pago sea online, los registros reales de procesamiento estarán representados por `Payment`.

---

# Paso 6 — Confirmación

Mostrar:

* cliente;
* productos;
* cantidades;
* subtotal;
* descuentos;
* cupón;
* costo de envío;
* total;
* entrega;
* pago.

Luego permitir crear el pedido.

Después de crearlo, navegar automáticamente al detalle.

---

# 3. PRODUCTOS

Crear una sección de catálogo.

## Tabla

Mostrar:

* descripción;
* categoría;
* precio actual;
* disponibilidad.

Opcionalmente mostrar como métricas derivadas:

* unidades vendidas;
* facturación histórica.

No mostrar:

* imagen;
* stock;
* SKU;
* variantes;
* marca;

porque no existen.

---

# Precio actual

`Product` tiene un historial de `Price`.

El precio actual debe obtenerse seleccionando el precio cuyo:

`sinceDate <= now`

y cuyo `sinceDate` sea el más reciente.

No asumir que `Price.price` directamente representa siempre el precio actual sin considerar `sinceDate`.

---

# Detalle del producto

Mostrar:

* descripción;
* categoría;
* disponibilidad;
* precio actual;
* historial de precios;
* unidades vendidas;
* pedidos en los que apareció.

El historial de precios puede construirse directamente con `Price[]`.

---

# Crear / editar producto

Campos disponibles:

* description;
* category;
* available.

La modificación de precio debe crear o administrar registros `Price` según la lógica definida por el backend.

No reemplazar conceptualmente el historial de precios por un simple atributo `product.price`.

---

# Categorías

Las categorías existen mediante `Category`.

Permitir gestionar:

* descripción de categoría;
* productos pertenecientes.

Cada producto debe pertenecer exactamente a una categoría.

---

# 4. PAGOS

Crear una pantalla orientada al monitoreo de pagos.

## KPIs

Mostrar:

* monto aprobado;
* pagos pendientes;
* pagos rechazados;
* pagos fallidos;
* pagos expirados.

Utilizar `Payment.status`.

## Tabla

Mostrar:

* ID abreviado;
* pedido;
* proveedor;
* referencia externa;
* monto;
* estado;
* fecha;
* última actualización.

## Filtros

* estado;
* proveedor;
* fecha.

No agregar filtro por método de tarjeta, banco, cuotas, etc., porque esos datos no existen.

---

# Detalle del pago

Mostrar:

* ID;
* pedido relacionado;
* provider;
* externalId;
* amount;
* status;
* createdAt;
* updatedAt.

Permitir navegar al pedido correspondiente.

Usar badges para:

PENDING
APPROVED
REJECTED
FAILED
EXPIRED

---

# 5. CLIENTES

Crear una sección simple de CRM.

## Tabla

Los datos persistidos disponibles son únicamente:

* nombre;
* apellido;
* teléfono.

A partir de las relaciones pueden calcularse:

* cantidad de pedidos;
* total gastado;
* ticket promedio;
* último pedido;
* cantidad de conversaciones.

Mostrar por ejemplo:

Cliente
Teléfono
Pedidos
Total gastado
Último pedido

---

# Perfil del cliente

Mostrar:

## Información

* nombre;
* apellido;
* teléfono.

## Métricas derivadas

* pedidos realizados;
* gasto total;
* ticket promedio;
* última compra.

## Pedidos

Mostrar historial de `Client.orders`.

## Conversaciones

Mostrar `Client.conversations`.

No mostrar:

* email;
* fecha de nacimiento;
* notas;
* tags;
* dirección personal;

porque no están modelados.

---

# 6. CUPONES

Crear una sección basada estrictamente en `Coupon`.

## Tabla

Mostrar:

* código;
* tipo;
* monto;
* usos disponibles;
* vencimiento;
* estado visual derivado.

## Estado visual derivado

El schema no contiene `active`.

Puede derivarse visualmente:

* Vencido → `dateOfExpiration < now`
* Agotado → `availableUses <= 0`
* Disponible → no vencido y con usos disponibles

Este estado NO debe guardarse como un atributo nuevo de `Coupon`.

---

# Crear cupón

Permitir configurar únicamente:

* couponCode;
* type;
* amount;
* availableUses;
* dateOfExpiration.

`type` es String y no enum.

No asumir que únicamente existirán `FIXED_AMOUNT` y `PERCENTAGE`, aunque pueden utilizarse como ejemplos si son los valores actualmente soportados por la lógica del backend.

---

# Historial de utilización

Utilizar `AppliedCoupon`.

Mostrar:

* pedido;
* código utilizado;
* tipo;
* monto;
* descuento real generado;
* fecha de aplicación.

---

# 7. CONVERSACIONES

Crear una interfaz similar a un inbox/chat de atención.

Pero utilizar únicamente datos que realmente existen.

Layout desktop:

[ Lista de conversaciones ] [ Conversación ] [ Contexto ]

---

# Lista de conversaciones

Para cada conversación mostrar:

* cliente si existe;
* canal;
* último mensaje;
* fecha del último mensaje;
* sentimiento general;
* última intención.

La fecha del último mensaje debe derivarse del `Message.createdAt` más reciente.

No mostrar contador de mensajes no leídos porque no existe esa información.

---

# Panel del chat

Mostrar `Message[]` ordenados por `createdAt`.

Cada mensaje posee:

* role;
* content;
* detectedIntent;
* sentiment;
* status;
* createdAt.

Utilizar `role` para distinguir visualmente los mensajes.

Los valores documentados actualmente son:

* USER
* AGENT
* SYSTEM

Pero `role` es un String abierto.

Por lo tanto, la UI debe soportar valores desconocidos sin romperse.

---

# Información contextual

Mostrar:

* cliente;
* teléfono;
* canal;
* sentimiento general;
* última intención;
* pedidos asociados a la conversación.

Una conversación puede tener múltiples pedidos:

`Conversation.orders`

Permitir abrir cualquiera de ellos.

---

# NO INVENTAR CONTROL HUMANO DEL AGENTE

Actualmente no existe ningún atributo como:

* handledByHuman;
* agentEnabled;
* conversationStatus;
* assignedUser;
* takeoverAt.

Por lo tanto, no implementar botones como:

"Tomar conversación"

"Devolver al agente"

"Pausar IA"

hasta que el modelo/backend soporte ese comportamiento.

---

# 8. CONFIGURACIÓN

Esta sección sí está soportada directamente por el modelo.

Utilizar:

`BusinessConfiguration`

## Datos generales

Mostrar y editar:

* businessName;
* minOrder;
* shippingCost;
* availableZone.

---

# Horarios

Utilizar `BusinessHours`.

Permitir administrar por día:

* día de la semana;
* hora de apertura;
* hora de cierre.

Utilizar exclusivamente `WeekDay`.

Los horarios están almacenados como String en formato:

`HH:MM`

La UI puede usar un time picker, pero debe convertir el resultado a ese formato.

---

# Direcciones

Utilizar `BusinessConfiguration.addresses`.

Permitir administrar:

* calle;
* número;
* piso;
* departamento;
* ciudad;
* provincia;
* código postal.

---

# RELACIONES ENTRE PANTALLAS

Las entidades relacionadas deben poder navegarse fácilmente.

Pedido → Cliente
Pedido → Conversación
Pedido → Pagos
Pedido → Cupón aplicado
Pedido → Productos

Cliente → Pedidos
Cliente → Conversaciones

Conversación → Cliente
Conversación → Pedidos

Pago → Pedido

Producto → Categoría
Producto → Pedidos

Cupón → Aplicaciones → Pedidos

Evitar que cada módulo parezca un CRUD aislado.

---

# DISEÑO

Quiero un panel SaaS moderno, profesional y orientado a operaciones.

Referencias conceptuales:

* Stripe
* Linear
* Shopify Admin
* Vercel

No copiar literalmente sus interfaces.

Usar:

* sidebar;
* header compacto;
* tablas bien diseñadas;
* badges;
* dropdown actions;
* dialogs;
* sheets;
* tooltips;
* skeleton loading;
* empty states;
* estados de error;
* toast notifications;
* breadcrumbs cuando agreguen contexto.

Evitar:

* exceso de cards;
* gradientes innecesarios;
* glassmorphism exagerado;
* sombras fuertes;
* elementos decorativos sin función;
* gráficos sin utilidad;
* diseño estilo plantilla administrativa genérica.

---

# PRIORIDADES DE UX

Las acciones que deben ser más rápidas son:

1. identificar pedidos nuevos;
2. ver pedidos en preparación;
3. cambiar el estado de un pedido;
4. crear un pedido manual;
5. encontrar un pedido;
6. revisar problemas de pagos;
7. marcar un producto disponible/no disponible;
8. revisar una conversación;
9. encontrar un cliente;
10. crear un cupón.

Diseñar la jerarquía de acciones alrededor de estas prioridades.

---

# RESPONSIVE

Prioridad:

1. Desktop
2. Tablet
3. Mobile

En desktop utilizar toda la información disponible.

En tablet reorganizar paneles manteniendo funcionalidad.

En mobile priorizar las acciones operativas principales y adaptar tablas cuando sea necesario.

---

# DATOS MOCK

Si el backend todavía no está disponible, generar mocks basados exclusivamente en este schema.

Usar contenido realista para un restaurante argentino.

Ejemplos de `Product.description`:

* Hamburguesa Clásica
* Hamburguesa Doble Bacon
* Pizza Napolitana
* Pizza Muzarella
* Papas con Cheddar
* Empanada de Carne
* Coca-Cola 500 ml

Categorías:

* Hamburguesas
* Pizzas
* Acompañamientos
* Bebidas

Clientes realistas:

* Martina López
* Nicolás Fernández
* Lucía Romero
* Tomás García

Canal:

* WHATSAPP

No crear atributos inexistentes solamente para enriquecer los mocks.

---

# ARQUITECTURA DE COMPONENTES

No desarrollar cada pantalla como una página aislada y duplicada.

Identificar componentes reutilizables como:

* `StatusBadge`
* `OrderStatusBadge`
* `PaymentStatusBadge`
* `Money`
* `DateTime`
* `ClientLink`
* `OrderLink`
* `ProductAvailabilityBadge`
* `MetricCard`
* `DataTable`
* `EmptyState`
* `SearchInput`
* `FilterBar`
* `OrderSummary`
* `PaymentSummary`

Los nombres son orientativos; adapta la arquitectura al stack existente.

---

# ANTES DE IMPLEMENTAR

Primero analiza el schema y presenta brevemente:

1. mapa de entidades;
2. relaciones relevantes;
3. navegación propuesta;
4. métricas calculables;
5. datos que deben calcularse en frontend/backend;
6. funcionalidades que NO pueden implementarse con el schema actual.

Después implementa.

No agregues campos al schema sin solicitarlo explícitamente.

No inventes datos para hacer que el diseño "se vea más completo".

Si una funcionalidad no es posible con el modelo actual, indícalo claramente y diseña únicamente lo que sí está respaldado por los datos.

El objetivo final debe ser un **producto SaaS coherente y operativo para un restaurante real**, no una colección de CRUDs generados automáticamente.
