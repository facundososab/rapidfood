"""Deterministic in-memory dataset for the mock client.

Built strictly from the Prisma schema — no invented fields. Argentine restaurant
content. Dates are relative to "now" so the dashboard time selectors and series
have meaningful data. Money is Decimal.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List

from . import dtos

D = Decimal


def _dt(days_ago: float, hour: int = 12, minute: int = 0) -> datetime:
    base = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    return base - timedelta(days=days_ago)


class Dataset:
    """Holds every collection. The mock client mutates this in place."""

    def __init__(self) -> None:
        self.categories: List[dtos.Category] = []
        self.products: List[dtos.Product] = []
        self.prices: List[dtos.Price] = []
        self.discounts: List[dtos.Discount] = []
        self.clients: List[dtos.Client] = []
        self.addresses: List[dtos.Address] = []
        self.orders: List[dtos.Order] = []
        self.order_lines: List[dtos.OrderLine] = []
        self.applied_coupons: List[dtos.AppliedCoupon] = []
        self.payments: List[dtos.Payment] = []
        self.coupons: List[dtos.Coupon] = []
        self.conversations: List[dtos.Conversation] = []
        self.messages: List[dtos.Message] = []
        self.business: dtos.BusinessConfiguration = None  # type: ignore
        self._seq = 0
        self._build()

    def next_id(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}-{self._seq:04d}"

    # ------------------------------------------------------------------
    def _build(self) -> None:
        cats = {
            "burgers": ("cat-burgers", "Hamburguesas"),
            "pizzas": ("cat-pizzas", "Pizzas"),
            "sides": ("cat-sides", "Acompañamientos"),
            "drinks": ("cat-drinks", "Bebidas"),
        }
        for cid, desc in cats.values():
            self.categories.append(dtos.Category(id=cid, description=desc))

# products: (id, name, description, category, [(days_ago, price), ...], available)
        product_spec = [
            ("prod-1", "Hamburguesa Clásica", "Medallón de carne, queso, lechuga y tomate", "cat-burgers", [(120, "5200"), (30, "5900")], True),
            ("prod-2", "Hamburguesa Doble Bacon", "Doble medallón, cheddar y bacon crocante", "cat-burgers", [(120, "7400"), (20, "8200")], True),
            ("prod-3", "Pizza Napolitana", "Masa con tomate, muzzarella y albahaca", "cat-pizzas", [(90, "8900"), (10, "9600")], True),
            ("prod-4", "Pizza Muzzarella", "Muzzarella, salsa de tomate y orégano", "cat-pizzas", [(90, "7600"), (10, "8100")], True),
            ("prod-5", "Papas con Cheddar", "Papas fritas con cheddar fundido", "cat-sides", [(120, "4200"), (15, "4800")], True),
            ("prod-6", "Empanada de Carne", "Empanada de carne cortada a cuchillo", "cat-sides", [(120, "1500"), (40, "1700")], True),
            ("prod-7", "Coca-Cola 500 ml", "Bebida gaseosa sabor cola 500 ml", "cat-drinks", [(200, "1800"), (25, "2100")], False),
        ]
        cat_by_id = {c.id: c for c in self.categories}
        for pid, name, desc, cat, prices, available in product_spec:
            prod = dtos.Product(id=pid, name=name, description=desc, available=available,
                                categoryId=cat, category=cat_by_id[cat],
                                imageUrl="https://picsum.photos/seed/rapidfood/400")
            for days_ago, price in prices:
                pr = dtos.Price(id=self.next_id("price"), productId=pid,
                                sinceDate=_dt(days_ago), price=D(price))
                self.prices.append(pr)
                prod.prices.append(pr)
            self.products.append(prod)

        self.discounts.append(dtos.Discount(id="disc-10", percentage=D("10")))

        client_spec = [
            ("cli-1", "Martina", "López", "+54 9 11 5555-1001"),
            ("cli-2", "Nicolás", "Fernández", "+54 9 11 5555-1002"),
            ("cli-3", "Lucía", "Romero", "+54 9 11 5555-1003"),
            ("cli-4", "Tomás", "García", "+54 9 11 5555-1004"),
            ("cli-5", "Sofía", "Martínez", "+54 9 11 5555-1005"),
            ("cli-6", "Julián", "Sosa", "+54 9 11 5555-1006"),
        ]
        for cid, name, last, phone in client_spec:
            self.clients.append(dtos.Client(id=cid, name=name, lastName=last, phoneNumber=phone))

        self.business = dtos.BusinessConfiguration(
            id="biz-1", businessName="Rapidfood Palermo", minOrder=D("6000"),
            shippingCost=D("1200"), availableZone="CABA — Palermo, Villa Crespo, Colegiales",
        )
        self.business.businessHours = [
            dtos.BusinessHours(id=self.next_id("bh"), openWeekDay=wd,
                               openFromHour="11:00", openToHour="23:30", businessConfigId="biz-1")
            for wd in ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY"]
        ]
        self.business.businessHours.append(
            dtos.BusinessHours(id=self.next_id("bh"), openWeekDay="SUNDAY",
                               openFromHour="18:00", openToHour="23:30", businessConfigId="biz-1"))
        self.addresses = [
            dtos.Address(id="addr-biz", street="Thames", streetNumber="1520", city="CABA",
                         province="Buenos Aires", postalCode="1414", businessConfigId="biz-1"),
        ]
        self.business.addresses = list(self.addresses)
        # delivery addresses (belong to business config per schema, referenced by orders)
        self.addresses.append(dtos.Address(id="addr-1", street="Gurruchaga", streetNumber="850",
                              floor="3", apartment="B", city="CABA", province="Buenos Aires",
                              postalCode="1414", businessConfigId="biz-1"))
        self.addresses.append(dtos.Address(id="addr-2", street="Córdoba", streetNumber="4200",
                              city="CABA", province="Buenos Aires", postalCode="1188",
                              businessConfigId="biz-1"))

        self.coupons = [
            dtos.Coupon(id="cou-1", couponCode="BIENVENIDO10", type="PERCENTAGE", amount=D("10"),
                        availableUses=40, dateOfExpiration=_dt(-60)),
            dtos.Coupon(id="cou-2", couponCode="ENVIOGRATIS", type="FIXED_AMOUNT", amount=D("1200"),
                        availableUses=0, dateOfExpiration=_dt(-30)),
            dtos.Coupon(id="cou-3", couponCode="VERANO2024", type="PERCENTAGE", amount=D("15"),
                        availableUses=12, dateOfExpiration=_dt(20)),
            dtos.Coupon(id="cou-4", couponCode="COMBO5000", type="FIXED_AMOUNT", amount=D("5000"),
                        availableUses=8, dateOfExpiration=None),
        ]

        self._build_orders()
        self._build_conversations()

    # ------------------------------------------------------------------
    def price_now(self, product_id: str) -> Decimal:
        prices = [p for p in self.prices if p.productId == product_id and p.sinceDate <= datetime.now()]
        if not prices:
            return D("0")
        return max(prices, key=lambda p: p.sinceDate).price

    def _mk_line(self, order_id, product_id, qty, in_draft=False, discount_id=None):
        unit = None if in_draft else self.price_now(product_id)
        subtotal = D("0") if unit is None else unit * qty
        if discount_id and unit is not None:
            disc = next((d for d in self.discounts if d.id == discount_id), None)
            if disc:
                subtotal = (subtotal * (D("100") - disc.percentage) / D("100")).quantize(D("0.01"))
        line = dtos.OrderLine(id=self.next_id("line"), orderId=order_id, productId=product_id,
                              quantity=qty, unitPrice=unit, subtotal=subtotal, discountId=discount_id)
        self.order_lines.append(line)
        return line

    def _build_orders(self) -> None:
        # (id, status, client, delivery, payment, days_ago, hour, lines[(prod,qty)],
        #   address, coupon_code, confirmed_days_ago, estimated, payments[(provider,status,amount_off)])
        specs = [
            ("ord-1001", "IN_PREPARATION", "cli-1", "DELIVERY", "ONLINE", 0, 12, [("prod-1", 2), ("prod-5", 1)], "addr-1", None, 0, 35, [("MercadoPago", "APPROVED", 0)]),
            ("ord-1002", "PENDING", "cli-2", "PICKUP", "CASH", 0, 13, [("prod-3", 1), ("prod-7", 2)], None, None, None, None, []),
            ("ord-1003", "READY", "cli-3", "DELIVERY", "ONLINE", 0, 11, [("prod-2", 1), ("prod-6", 3)], "addr-2", "BIENVENIDO10", 0, 25, [("MercadoPago", "APPROVED", 0)]),
            ("ord-1004", "DELIVERED", "cli-4", "DELIVERY", "CASH", 1, 20, [("prod-4", 2)], "addr-1", None, 1, 40, []),
            ("ord-1005", "CANCELLED", "cli-5", "PICKUP", "ONLINE", 1, 21, [("prod-1", 1)], None, None, None, None, [("MercadoPago", "REJECTED", 0)]),
            ("ord-1006", "CONFIRMED", "cli-1", "DELIVERY", "ONLINE", 0, 14, [("prod-3", 2), ("prod-4", 1), ("prod-7", 3)], "addr-2", None, 0, 30, [("MercadoPago", "APPROVED", 0)]),
            ("ord-1007", "PAID", "cli-6", "PICKUP", "ONLINE", 0, 10, [("prod-2", 2)], None, None, None, None, [("MercadoPago", "APPROVED", 0)]),
            ("ord-1008", "PICKED_UP", "cli-2", "PICKUP", "CASH", 2, 19, [("prod-5", 2), ("prod-6", 6)], None, "COMBO5000", 2, 20, []),
            ("ord-1009", "DELIVERED", "cli-3", "DELIVERY", "ONLINE", 3, 20, [("prod-1", 1), ("prod-2", 1), ("prod-7", 2)], "addr-1", None, 3, 45, [("MercadoPago", "APPROVED", 0)]),
            ("ord-1010", "DELIVERED", None, "DELIVERY", "CASH", 4, 21, [("prod-4", 1), ("prod-5", 1)], "addr-2", None, 4, 35, []),
            ("ord-1011", "DRAFT", "cli-4", None, None, 0, 15, [("prod-1", 1), ("prod-3", 1)], None, None, None, None, []),
            ("ord-1012", "PENDING", None, "DELIVERY", "ONLINE", 0, 16, [("prod-2", 1), ("prod-6", 2)], "addr-1", None, None, None, [("MercadoPago", "PENDING", 0)]),
            ("ord-1013", "IN_PREPARATION", "cli-5", "PICKUP", "CASH", 0, 12, [("prod-3", 1), ("prod-4", 1)], None, None, 0, 25, []),
            ("ord-1014", "DELIVERED", "cli-6", "DELIVERY", "ONLINE", 6, 20, [("prod-1", 3)], "addr-2", "VERANO2024", 6, 40, [("MercadoPago", "APPROVED", 0)]),
            ("ord-1015", "DELIVERED", "cli-1", "DELIVERY", "ONLINE", 8, 21, [("prod-3", 2), ("prod-7", 2)], "addr-1", None, 8, 35, [("MercadoPago", "APPROVED", 0)]),
            ("ord-1016", "PICKED_UP", "cli-2", "PICKUP", "CASH", 10, 13, [("prod-5", 3)], None, None, 10, 20, []),
            ("ord-1017", "DELIVERED", "cli-3", "DELIVERY", "ONLINE", 12, 20, [("prod-2", 2), ("prod-5", 1)], "addr-2", None, 12, 40, [("MercadoPago", "APPROVED", 0), ("MercadoPago", "FAILED", 0)]),
            ("ord-1018", "CANCELLED", "cli-4", "DELIVERY", "ONLINE", 14, 19, [("prod-4", 1)], "addr-1", None, None, None, [("MercadoPago", "EXPIRED", 0)]),
            ("ord-1019", "DELIVERED", "cli-5", "DELIVERY", "CASH", 18, 20, [("prod-1", 2), ("prod-6", 4)], "addr-2", None, 18, 35, []),
            ("ord-1020", "DELIVERED", "cli-6", "PICKUP", "ONLINE", 22, 12, [("prod-3", 1), ("prod-4", 1)], None, None, 22, 25, [("MercadoPago", "APPROVED", 0)]),
            ("ord-1021", "DELIVERED", "cli-1", "DELIVERY", "ONLINE", 26, 21, [("prod-2", 1), ("prod-7", 3)], "addr-1", None, 26, 40, [("MercadoPago", "APPROVED", 0)]),
        ]
        cli_by_id = {c.id: c for c in self.clients}
        addr_by_id = {a.id: a for a in self.addresses}
        for spec in specs:
            (oid, status, cli, delivery, payment, days_ago, hour, lines, addr,
             coupon_code, conf_ago, estimated, pays) = spec
            created = _dt(days_ago, hour, 0)
            is_draft = status == "DRAFT"
            order = dtos.Order(
                id=oid, status=status, subtotal=D("0"), discount=D("0"), createdAt=created,
                estimatedTime=estimated, deliveryType=delivery, paymentType=payment,
                clientId=cli, addressId=addr, confirmedAt=_dt(conf_ago, hour, 20) if conf_ago is not None else None,
                client=cli_by_id.get(cli), address=addr_by_id.get(addr),
            )
            for pid, qty in lines:
                order.lines.append(self._mk_line(oid, pid, qty, in_draft=is_draft))
            subtotal = sum((ln.subtotal for ln in order.lines), D("0"))
            order.subtotal = subtotal
            # coupon snapshot (AppliedCoupon)
            discount = D("0")
            if coupon_code:
                cou = next((c for c in self.coupons if c.couponCode == coupon_code), None)
                if cou:
                    if cou.type == "PERCENTAGE":
                        discount = (subtotal * cou.amount / D("100")).quantize(D("0.01"))
                    else:
                        discount = min(cou.amount, subtotal)
                    ac = dtos.AppliedCoupon(
                        id=self.next_id("ac"), orderId=oid, couponId=cou.id,
                        couponCode=cou.couponCode, type=cou.type, amount=cou.amount,
                        discountAmount=discount, availableUses=cou.availableUses,
                        dateOfExpiration=cou.dateOfExpiration, appliedAt=created)
                    self.applied_coupons.append(ac)
                    order.appliedCoupons.append(ac)
                    order.appliedCouponId = ac.id
            order.discount = discount
            if is_draft:
                order.totalAmount = None
                order.shippingCost = None
            else:
                shipping = self.business.shippingCost if delivery == "DELIVERY" else D("0")
                order.shippingCost = shipping
                order.totalAmount = subtotal - discount + shipping
            for provider, pstatus, _off in pays:
                amount = order.totalAmount if order.totalAmount is not None else subtotal
                pay = dtos.Payment(
                    id=self.next_id("pay"), orderId=oid, provider=provider, status=pstatus,
                    amount=amount, externalId=f"MP-{self._seq:06d}",
                    createdAt=created + timedelta(minutes=2),
                    updatedAt=created + timedelta(minutes=8))
                self.payments.append(pay)
                order.payments.append(pay)
            self.orders.append(order)

    def _build_conversations(self) -> None:
        cli_by_id = {c.id: c for c in self.clients}
        ord_by_id = {o.id: o for o in self.orders}
        conv_spec = [
            ("conv-1", "cli-1", "WHATSAPP", "positive", "crear_pedido", ["ord-1001"], [
                ("USER", "Hola! Quiero pedir 2 hamburguesas clásicas y papas", "crear_pedido", "positive"),
                ("AGENT", "¡Hola Martina! Perfecto, 2 Hamburguesas Clásicas y 1 Papas con Cheddar. ¿Envío o retiro?", "confirmar_items", "positive"),
                ("USER", "Envío a Gurruchaga 850", "definir_entrega", "neutral"),
                ("AGENT", "Listo, tu pedido está en preparación. Total $13.400. Tiempo estimado 35 min.", "confirmar_pedido", "positive"),
            ]),
            ("conv-2", "cli-2", "WHATSAPP", "neutral", "consultar_estado", ["ord-1002", "ord-1008"], [
                ("USER", "Buenas, tienen pizza napolitana?", "consultar_producto", "neutral"),
                ("AGENT", "¡Sí! Pizza Napolitana $9.600. ¿Te la preparo?", "ofrecer_producto", "positive"),
                ("USER", "Dale, y 2 coca colas", "crear_pedido", "positive"),
                ("SYSTEM", "Pedido ord-1002 creado en estado PENDING", None, None),
            ]),
            ("conv-3", "cli-3", "WHATSAPP", "negative", "reclamo", ["ord-1003"], [
                ("USER", "Mi pedido está tardando mucho", "reclamo", "negative"),
                ("AGENT", "Lamento la demora, tu pedido ya está listo y sale en breve.", "gestionar_reclamo", "neutral"),
                ("ESCALATION", "Conversación marcada con sentimiento negativo", None, "negative"),
            ]),
            ("conv-4", None, "WHATSAPP", "neutral", "consultar_horario", [], [
                ("USER", "Hasta qué hora están abiertos?", "consultar_horario", "neutral"),
                ("AGENT", "Atendemos hasta las 23:30 de lunes a sábado.", "informar_horario", "positive"),
            ]),
        ]
        for cid, cli, channel, sentiment, intent, order_ids, msgs in conv_spec:
            conv = dtos.Conversation(id=cid, channel=channel, overallSentiment=sentiment,
                                     lastIntent=intent, clientId=cli, client=cli_by_id.get(cli))
            base = _dt(0, 12, 0)
            for i, (role, content, di, sent) in enumerate(msgs):
                m = dtos.Message(id=self.next_id("msg"), conversationId=cid, role=role,
                                 content=content, detectedIntent=di, sentiment=sent,
                                 status="delivered", createdAt=base + timedelta(minutes=i * 3))
                self.messages.append(m)
                conv.messages.append(m)
            for oid in order_ids:
                if oid in ord_by_id:
                    ord_by_id[oid].conversationId = cid
                    ord_by_id[oid].origin = "AGENT"
                    conv.orders.append(ord_by_id[oid])
            self.conversations.append(conv)


_DATASET: Dataset = None  # type: ignore


def get_dataset() -> Dataset:
    global _DATASET
    if _DATASET is None:
        _DATASET = Dataset()
    return _DATASET
