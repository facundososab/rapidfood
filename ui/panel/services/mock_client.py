"""In-memory implementation of RapidfoodClient, seeded from the Prisma schema.

Mutations (create order/client, status changes, availability toggles, price/coupon
edits) persist for the life of the process. Swap for HttpRapidfoodClient via the
RAPIDFOOD_CLIENT setting without touching views/templates.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from . import dtos
from .client import CouponValidation, Page, RapidfoodClient
from .seed import get_dataset

D = Decimal


def _paginate(items: list, page: int, page_size: int) -> Page:
    total = len(items)
    start = (page - 1) * page_size
    return Page(items=items[start:start + page_size], total=total, page=page, page_size=page_size)


import uuid

class MockRapidfoodClient(RapidfoodClient):
    def __init__(self) -> None:
        self.db = get_dataset()
        self.ingredients: List[dtos.Ingredient] = []
        self.variants: List[dtos.Variant] = []
        self.modifier_groups: List[dtos.ModifierGroup] = []
        self.modifier_options: List[dtos.ModifierOption] = []

    # ---- Orders -----------------------------------------------------------
    def all_orders(self) -> List[dtos.Order]:
        return list(self.db.orders)

    def list_orders(self, *, status=None, delivery_type=None, payment_type=None,
                    client_id=None, search=None, date_from=None, date_to=None,
                    page=1, page_size=15) -> Page:
        rows = sorted(self.db.orders, key=lambda o: o.createdAt, reverse=True)
        if status:
            rows = [o for o in rows if o.status == status]
        if delivery_type:
            rows = [o for o in rows if o.deliveryType == delivery_type]
        if payment_type:
            rows = [o for o in rows if o.paymentType == payment_type]
        if client_id:
            rows = [o for o in rows if o.clientId == client_id]
        if date_from:
            rows = [o for o in rows if o.createdAt >= date_from]
        if date_to:
            rows = [o for o in rows if o.createdAt <= date_to]
        if search:
            q = search.lower().strip()
            def match(o: dtos.Order) -> bool:
                if q in o.id.lower():
                    return True
                c = o.client
                if c and (q in c.name.lower() or q in c.lastName.lower()
                          or q in c.phoneNumber.lower()):
                    return True
                return False
            rows = [o for o in rows if match(o)]
        return _paginate(rows, page, page_size)

    def get_order(self, order_id: str) -> Optional[dtos.Order]:
        return next((o for o in self.db.orders if o.id == order_id), None)

    def update_order_status(self, order_id: str, status: str) -> dtos.Order:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("order not found")
        order.status = status
        if status == "CONFIRMED" and order.confirmedAt is None:
            order.confirmedAt = datetime.now()
        return order

    def cancel_order(self, order_id: str) -> dtos.Order:
        order = self.get_order(order_id)
        if order is None:
            raise ValueError("order not found")
        order.status = "CANCELLED"
        return order

    def create_order(self, payload: dict) -> dtos.Order:
        db = self.db
        oid = db.next_id("ord")
        client = self.get_client(payload["client_id"]) if payload.get("client_id") else None
        delivery = payload.get("delivery_type")
        addr_id = payload.get("address_id")
        order = dtos.Order(
            id=oid, status="PENDING", subtotal=D("0"), discount=D("0"),
            createdAt=datetime.now(), origin=payload.get("origin") or "IN_PLACE",
            deliveryType=delivery,
            paymentType=payload.get("payment_type"), clientId=payload.get("client_id"),
            addressId=addr_id, client=client,
            address=next((a for a in db.addresses if a.id == addr_id), None) if addr_id else None,
        )
        subtotal = D("0")
        for item in payload.get("lines", []):
            unit = db.price_now(item["product_id"])
            qty = int(item["quantity"])
            line = dtos.OrderLine(id=db.next_id("line"), orderId=oid,
                                  productId=item["product_id"], quantity=qty,
                                  unitPrice=unit, subtotal=unit * qty,
                                  product=self.get_product(item["product_id"]))
            db.order_lines.append(line)
            order.lines.append(line)
            subtotal += line.subtotal
        order.subtotal = subtotal
        discount = D("0")
        code = payload.get("coupon_code")
        if code:
            validation = self.validate_coupon(code, subtotal)
            if validation.valid and validation.coupon:
                discount = validation.discount_amount
                cou = validation.coupon
                ac = dtos.AppliedCoupon(
                    id=db.next_id("ac"), orderId=oid, couponId=cou.id,
                    couponCode=cou.couponCode, type=cou.type, amount=cou.amount,
                    discountAmount=discount, availableUses=cou.availableUses,
                    dateOfExpiration=cou.dateOfExpiration, appliedAt=datetime.now())
                db.applied_coupons.append(ac)
                order.appliedCoupons.append(ac)
                order.appliedCouponId = ac.id
        order.discount = discount
        shipping = db.business.shippingCost if delivery == "DELIVERY" else D("0")
        order.shippingCost = shipping
        order.totalAmount = subtotal - discount + shipping
        db.orders.append(order)
        return order

    # ---- Products ---------------------------------------------------------
    def _decorate_product(self, p: dtos.Product) -> dtos.Product:
        if p.category is None:
            p.category = next((c for c in self.db.categories if c.id == p.categoryId), None)
        return p

    def list_products(self, *, search=None, category_id=None, only_available=False,
                       page=1, page_size=20) -> Page:
        rows = [self._decorate_product(p) for p in self.db.products]
        if search:
            q = search.lower().strip()
            rows = [p for p in rows if q in p.name.lower() or q in p.description.lower()
                    or (p.category and q in p.category.description.lower())]
        if category_id:
            rows = [p for p in rows if p.categoryId == category_id]
        if only_available:
            rows = [p for p in rows if p.available]
        rows.sort(key=lambda p: p.name)
        return _paginate(rows, page, page_size)

    def get_product(self, product_id: str) -> Optional[dtos.Product]:
        p = next((p for p in self.db.products if p.id == product_id), None)
        return self._decorate_product(p) if p else None

    def set_product_availability(self, product_id: str, available: bool) -> dtos.Product:
        p = self.get_product(product_id)
        if p is None:
            raise ValueError("product not found")
        p.available = available
        return p

    def delete_product(self, product_id: str) -> None:
        db = self.db
        if all(p.id != product_id for p in db.products):
            raise ValueError("product not found")
        if any(line.productId == product_id for line in db.order_lines):
            raise ValueError("product in use")
        db.products = [p for p in db.products if p.id != product_id]
        db.prices = [p for p in db.prices if p.productId != product_id]
        db.discounts = [d for d in db.discounts if d.productId != product_id]

    def save_product(self, payload: dict) -> dtos.Product:
        db = self.db
        pid = payload.get("id")
        if pid:
            p = self.get_product(pid)
            p.name = payload["name"]
            p.description = payload["description"]
            p.imageUrl = payload.get("image_url") or p.imageUrl
            p.categoryId = payload["category_id"]
            p.available = payload.get("available", p.available)
            p.category = next((c for c in db.categories if c.id == p.categoryId), None)
            return p
        p = dtos.Product(id=db.next_id("prod"), name=payload["name"],
                         description=payload["description"],
                         available=payload.get("available", True),
                         categoryId=payload["category_id"], imageUrl=payload.get("image_url"))
        p.category = next((c for c in db.categories if c.id == p.categoryId), None)
        if payload.get("price"):
            pr = dtos.Price(id=db.next_id("price"), productId=p.id,
                            sinceDate=datetime.now(), price=D(str(payload["price"])))
            db.prices.append(pr)
            p.prices.append(pr)
        db.products.append(p)
        return p

    def add_product_price(self, product_id: str, price) -> dtos.Product:
        db = self.db
        p = self.get_product(product_id)
        pr = dtos.Price(id=db.next_id("price"), productId=product_id,
                        sinceDate=datetime.now(), price=D(str(price)))
        db.prices.append(pr)
        p.prices.append(pr)
        return p

    def list_categories(self) -> List[dtos.Category]:
        return list(self.db.categories)

    def save_category(self, payload: dict) -> dtos.Category:
        db = self.db
        cid = payload.get("id")
        if cid:
            c = next((c for c in db.categories if c.id == cid), None)
            c.description = payload["description"]
            return c
        c = dtos.Category(id=db.next_id("cat"), description=payload["description"])
        db.categories.append(c)
        return c

    # ---- Variants & Ingredients ------------------------------------------
    def list_ingredients(self):
        return list(self.ingredients)

    def create_ingredient(self, payload):
        ing = dtos.Ingredient(id=str(uuid.uuid4()), name=payload["name"])
        self.ingredients.append(ing)
        return ing

    def update_ingredient(self, ingredient_id, payload):
        ing = next((i for i in self.ingredients if i.id == ingredient_id), None)
        if ing:
            ing.name = payload.get("name", ing.name)
        return ing

    def create_variant(self, product_id, payload):
        var = dtos.Variant(id=str(uuid.uuid4()), name=payload["name"], available=True, currentPrice=D(str(payload["initial_price"])))
        self.variants.append(var)
        p = self.get_product(product_id)
        if p: p.variants.append(var)
        return var

    def update_variant(self, variant_id, payload):
        var = next((v for v in self.variants if v.id == variant_id), None)
        if var:
            var.name = payload.get("name", var.name)
            var.available = payload.get("available", var.available)
        return var

    def set_variant_price(self, variant_id, price):
        var = next((v for v in self.variants if v.id == variant_id), None)
        if var: var.currentPrice = D(str(price))

    def set_variant_ingredients(self, variant_id, payload):
        return []

    def create_modifier_group(self, product_id, payload):
        mg = dtos.ModifierGroup(id=str(uuid.uuid4()), name=payload["name"], minSelections=payload.get("min_selections", 0), maxSelections=payload.get("max_selections", 1))
        self.modifier_groups.append(mg)
        return mg

    def update_modifier_group(self, group_id, payload):
        mg = next((g for g in self.modifier_groups if g.id == group_id), None)
        if mg:
            mg.name = payload.get("name", mg.name)
            mg.minSelections = payload.get("min_selections", mg.minSelections)
            mg.maxSelections = payload.get("max_selections", mg.maxSelections)
        return mg

    def create_modifier_option(self, group_id, payload):
        mo = dtos.ModifierOption(id=str(uuid.uuid4()), name=payload["name"], priceDelta=D(str(payload["price_delta"])), available=True)
        self.modifier_options.append(mo)
        return mo

    def update_modifier_option(self, option_id, payload):
        mo = next((o for o in self.modifier_options if o.id == option_id), None)
        if mo:
            mo.name = payload.get("name", mo.name)
            if "price_delta" in payload:
                mo.priceDelta = D(str(payload["price_delta"]))
            mo.available = payload.get("available", mo.available)
        return mo

    # ---- Payments ---------------------------------------------------------
    def all_payments(self) -> List[dtos.Payment]:
        return list(self.db.payments)

    def list_payments(self, *, status=None, provider=None, date_from=None,
                      date_to=None, page=1, page_size=15) -> Page:
        rows = sorted(self.db.payments, key=lambda p: p.createdAt, reverse=True)
        if status:
            rows = [p for p in rows if p.status == status]
        if provider:
            rows = [p for p in rows if provider.lower() in p.provider.lower()]
        if date_from:
            rows = [p for p in rows if p.createdAt >= date_from]
        if date_to:
            rows = [p for p in rows if p.createdAt <= date_to]
        return _paginate(rows, page, page_size)

    def get_payment(self, payment_id: str) -> Optional[dtos.Payment]:
        return next((p for p in self.db.payments if p.id == payment_id), None)

    # ---- Clients ----------------------------------------------------------
    def list_clients(self, *, search=None, page=1, page_size=15) -> Page:
        rows = list(self.db.clients)
        if search:
            q = search.lower().strip()
            rows = [c for c in rows if q in c.name.lower() or q in c.lastName.lower()
                    or q in c.phoneNumber.lower()]
        rows.sort(key=lambda c: (c.name, c.lastName))
        return _paginate(rows, page, page_size)

    def get_client(self, client_id: str) -> Optional[dtos.Client]:
        return next((c for c in self.db.clients if c.id == client_id), None)

    def delete_client(self, client_id: str) -> None:
        db = self.db
        if all(c.id != client_id for c in db.clients):
            raise ValueError("client not found")
        db.clients = [c for c in db.clients if c.id != client_id]

    def create_client(self, name: str, last_name: str, phone: str) -> dtos.Client:
        c = dtos.Client(id=self.db.next_id("cli"), name=name, lastName=last_name,
                        phoneNumber=phone)
        self.db.clients.append(c)
        return c

    def search_clients(self, query: str) -> List[dtos.Client]:
        return self.list_clients(search=query, page=1, page_size=8).items

    def create_address(self, payload: dict) -> dtos.Address:
        db = self.db
        addr = dtos.Address(
            id=db.next_id("addr"),
            street=payload.get("street", ""),
            streetNumber=payload.get("street_number", ""),
            city=payload.get("city", ""),
            province=payload.get("province", ""),
            floor=payload.get("floor") or None,
            apartment=payload.get("apartment") or None,
            postalCode=payload.get("postal_code") or None,
        )
        db.addresses.append(addr)
        return addr

    # ---- Coupons ----------------------------------------------------------
    def list_coupons(self) -> List[dtos.Coupon]:
        return list(self.db.coupons)

    def get_coupon(self, coupon_id: str) -> Optional[dtos.Coupon]:
        return next((c for c in self.db.coupons if c.id == coupon_id), None)

    def get_coupon_by_code(self, code: str) -> Optional[dtos.Coupon]:
        return next((c for c in self.db.coupons if c.couponCode.lower() == code.lower()), None)

    def save_coupon(self, payload: dict) -> dtos.Coupon:
        db = self.db
        cid = payload.get("id")
        if cid:
            c = self.get_coupon(cid)
            c.couponCode = payload["couponCode"]
            c.type = payload["type"]
            c.amount = D(str(payload["amount"]))
            c.availableUses = int(payload["availableUses"])
            c.dateOfExpiration = payload.get("dateOfExpiration")
            return c
        c = dtos.Coupon(id=db.next_id("cou"), couponCode=payload["couponCode"],
                        type=payload["type"], amount=D(str(payload["amount"])),
                        availableUses=int(payload["availableUses"]),
                        dateOfExpiration=payload.get("dateOfExpiration"))
        db.coupons.append(c)
        return c

    def validate_coupon(self, code: str, subtotal) -> CouponValidation:
        cou = self.get_coupon_by_code(code)
        if cou is None:
            return CouponValidation(valid=False, reason="El cupón no existe.")
        if cou.dateOfExpiration is not None and cou.dateOfExpiration < datetime.now():
            return CouponValidation(valid=False, reason="El cupón está vencido.", coupon=cou)
        if cou.availableUses <= 0:
            return CouponValidation(valid=False, reason="El cupón no tiene usos disponibles.", coupon=cou)
        subtotal = D(str(subtotal))
        if cou.type == "PERCENTAGE":
            discount = (subtotal * cou.amount / D("100")).quantize(D("0.01"))
        else:
            discount = min(cou.amount, subtotal)
        return CouponValidation(valid=True, coupon=cou, discount_amount=discount)

    def list_applied_coupons(self, *, coupon_id=None) -> List[dtos.AppliedCoupon]:
        rows = sorted(self.db.applied_coupons, key=lambda a: a.appliedAt, reverse=True)
        if coupon_id:
            rows = [a for a in rows if a.couponId == coupon_id]
        return rows

    # ---- Conversations ----------------------------------------------------
    def list_conversations(self) -> List[dtos.Conversation]:
        def last_at(c: dtos.Conversation):
            return max((m.createdAt for m in c.messages), default=datetime.min)
        return sorted(self.db.conversations, key=last_at, reverse=True)

    def get_conversation(self, conversation_id: str) -> Optional[dtos.Conversation]:
        return next((c for c in self.db.conversations if c.id == conversation_id), None)

    # ---- Business configuration ------------------------------------------
    def get_business_config(self) -> dtos.BusinessConfiguration:
        return self.db.business

    def save_business_config(self, payload: dict) -> dtos.BusinessConfiguration:
        biz = self.db.business
        biz.businessName = payload.get("businessName", biz.businessName)
        if payload.get("minOrder") is not None:
            biz.minOrder = D(str(payload["minOrder"]))
        if payload.get("shippingCost") is not None:
            biz.shippingCost = D(str(payload["shippingCost"]))
        biz.availableZone = payload.get("availableZone", biz.availableZone)
        return biz

    def save_business_hours(self, business_config_id: str, hours: list) -> None:
        biz = self.db.business
        biz.businessHours = [
            dtos.BusinessHours(
                id=self.db.next_id("bh"),
                openWeekDay=h["openWeekDay"],
                openFromHour=h["openFromHour"],
                openToHour=h["openToHour"],
                businessConfigId=business_config_id
            )
            for h in hours
        ]

    def create_business_address(self, business_config_id: str, payload: dict) -> dtos.Address:
        new_id = str(uuid.uuid4())
        address = dtos.Address(
            id=new_id, street=payload["street"], streetNumber=payload["streetNumber"],
            city=payload["city"], province=payload["province"],
            floor=payload.get("floor"), apartment=payload.get("apartment"),
            postalCode=payload.get("postalCode")
        )
        self.mock_business.addresses.append(address)
        return address

    def update_business_address(self, business_config_id: str, address_id: str, payload: dict) -> dtos.Address:
        for idx, addr in enumerate(self.mock_business.addresses):
            if addr.id == address_id:
                updated = dtos.Address(
                    id=address_id, street=payload["street"], streetNumber=payload["streetNumber"],
                    city=payload["city"], province=payload["province"],
                    floor=payload.get("floor"), apartment=payload.get("apartment"),
                    postalCode=payload.get("postalCode")
                )
                self.mock_business.addresses[idx] = updated
                return updated
        raise RuntimeError("Address not found")

    def delete_business_address(self, business_config_id: str, address_id: str) -> None:
        biz = self.db.business
        biz.addresses = [a for a in biz.addresses if a.id != address_id]

    # ---- Delivery configuration ------------------------------------------
