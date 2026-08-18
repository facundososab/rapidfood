"""HttpRapidfoodClient — consumes the real backend API.

This is the production implementation: it maps each interface method to an HTTP
call against the backend that owns the domain/Prisma/PostgreSQL, and parses the
JSON responses back into the same DTOs the mock returns. It deliberately does NOT
reimplement any business rule — it only transports and maps.

Products and orders are wired to the real catalog/order endpoints
(``api/catalog/*``, ``api/orders/*``) mapping their canonical snake_case /
``state`` payloads into the UI DTOs. The remaining modules (clients, coupons,
payments, conversations, business configuration) have no backend endpoints yet,
so their read methods return empty/neutral values to keep the panel navigable.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from . import dtos
from .client import CouponValidation, Page, RapidfoodClient


def _parse_dt(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    # The rest of the panel works with local naive datetimes (mock uses
    # datetime.now()), so drop tz info to keep comparisons consistent.
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _dec(value):
    return None if value is None else Decimal(str(value))


def _paginate_items(items: list, page: int, page_size: int) -> Page:
    total = len(items)
    start = (page - 1) * page_size
    return Page(items=items[start:start + page_size], total=total, page=page, page_size=page_size)


class HttpRapidfoodClient(RapidfoodClient):
    def __init__(self, base_url: str, token: str = "", session=None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        if session is None:
            import requests  # imported lazily so the mock path needs no dependency

            session = requests.Session()
            if token:
                session.headers["Authorization"] = f"Bearer {token}"
        self.session = session
        self._cats = None

    # -- transport helpers --------------------------------------------------
    def _get(self, path: str, **params) -> object:
        clean = {k: v for k, v in params.items() if v not in (None, "")}
        resp = self.session.get(f"{self.base_url}{path}", params=clean, timeout=15)
        self._raise_if_error(resp)
        return resp.json()

    def _post(self, path: str, payload: dict) -> object:
        resp = self.session.post(f"{self.base_url}{path}", json=payload, timeout=15)
        self._raise_if_error(resp)
        return resp.json()

    def _patch(self, path: str, payload: dict) -> object:
        resp = self.session.patch(f"{self.base_url}{path}", json=payload, timeout=15)
        self._raise_if_error(resp)
        return resp.json()

    @staticmethod
    def _raise_if_error(resp) -> None:
        if resp.ok:
            return
        try:
            body = resp.json()
            message = body.get("detail") or body.get("error") or resp.text
        except Exception:
            message = resp.text
        raise RuntimeError(f"{resp.request.method} {resp.url} -> {resp.status_code}: {message}")

    # -- mappers (JSON -> DTO) ---------------------------------------------
    def _client(self, d) -> Optional[dtos.Client]:
        if not d:
            return None
        return dtos.Client(id=d["id"], name=d["name"], lastName=d["lastName"],
                           phoneNumber=d["phoneNumber"])

    def _category(self, d) -> Optional[dtos.Category]:
        return None if not d else dtos.Category(id=d["id"], description=d["description"])

    def _price(self, d) -> dtos.Price:
        return dtos.Price(id=d["id"], productId=d["product_id"],
                          sinceDate=_parse_dt(d["since_date"]), price=_dec(d["price"]))

    def _product(self, d) -> Optional[dtos.Product]:
        if not d:
            return None
        state = d.get("state")
        available = d.get("available")
        if available is None:
            available = state == "available"
        return dtos.Product(id=d["id"], name=d["name"], description=d["description"], available=bool(available),
                            categoryId=d["category_id"], category=self._category(d.get("category")),
                            prices=[self._price(p) for p in d.get("prices", [])])

    def _line(self, d) -> dtos.OrderLine:
        return dtos.OrderLine(id=d["id"], orderId=d["order_id"], productId=d["product_id"],
                              quantity=d["quantity"], subtotal=_dec(d["subtotal"]),
                              unitPrice=_dec(d.get("unit_price")), discountId=d.get("discount_id"),
                              product=self._product(d.get("product")))

    def _applied_coupon(self, d) -> dtos.AppliedCoupon:
        return dtos.AppliedCoupon(id=d["id"], orderId=d["orderId"], couponId=d.get("couponId"),
                                  couponCode=d["couponCode"], type=d["type"], amount=_dec(d["amount"]),
                                  discountAmount=_dec(d["discountAmount"]), availableUses=d["availableUses"],
                                  dateOfExpiration=_parse_dt(d.get("dateOfExpiration")),
                                  appliedAt=_parse_dt(d["appliedAt"]))

    def _payment(self, d) -> dtos.Payment:
        return dtos.Payment(id=d["id"], orderId=d["orderId"], provider=d["provider"],
                            status=d["status"], amount=_dec(d["amount"]), externalId=d.get("externalId"),
                            createdAt=_parse_dt(d["createdAt"]), updatedAt=_parse_dt(d["updatedAt"]))

    def _address(self, d) -> Optional[dtos.Address]:
        if not d:
            return None
        return dtos.Address(id=d["id"], street=d["street"], streetNumber=d["streetNumber"],
                            city=d["city"], province=d["province"], floor=d.get("floor"),
                            apartment=d.get("apartment"), postalCode=d.get("postalCode"))

    def _order(self, d) -> Optional[dtos.Order]:
        if not d:
            return None
        return dtos.Order(
            id=d["id"], status=d["status"], subtotal=_dec(d["subtotal"]), discount=_dec(d["discount"]),
            createdAt=_parse_dt(d["created_at"]), estimatedTime=d.get("estimated_time"),
            deliveryType=d.get("delivery_type"), paymentType=d.get("payment_type"),
            shippingCost=_dec(d.get("shipping_cost")), totalAmount=_dec(d.get("total_amount")),
            clientId=d.get("client_id"), addressId=d.get("address_id"),
            conversationId=d.get("conversation_id"), appliedCouponId=d.get("applied_coupon_id"),
            confirmedAt=_parse_dt(d.get("confirmed_at")), client=self._client(d.get("client")),
            address=self._address(d.get("address")),
            lines=[self._line(x) for x in d.get("lines", [])],
            appliedCoupons=[self._applied_coupon(x) for x in d.get("appliedCoupons", [])],
            payments=[self._payment(x) for x in d.get("payments", [])])

    def _coupon(self, d) -> Optional[dtos.Coupon]:
        if not d:
            return None
        return dtos.Coupon(id=d["id"], couponCode=d["couponCode"], type=d["type"],
                           amount=_dec(d["amount"]), availableUses=d["availableUses"],
                           dateOfExpiration=_parse_dt(d.get("dateOfExpiration")))

    def _message(self, d) -> dtos.Message:
        return dtos.Message(id=d["id"], conversationId=d["conversationId"], role=d["role"],
                            content=d["content"], detectedIntent=d.get("detectedIntent"),
                            sentiment=d.get("sentiment"), status=d.get("status"),
                            createdAt=_parse_dt(d["createdAt"]))

    def _conversation(self, d) -> Optional[dtos.Conversation]:
        if not d:
            return None
        return dtos.Conversation(id=d["id"], channel=d["channel"],
                                 overallSentiment=d.get("overallSentiment"),
                                 lastIntent=d.get("lastIntent"), clientId=d.get("clientId"),
                                 client=self._client(d.get("client")),
                                 messages=[self._message(m) for m in d.get("messages", [])],
                                 orders=[self._order(o) for o in d.get("orders", [])])

    def _page(self, d, mapper) -> Page:
        return Page(items=[mapper(x) for x in d.get("items", [])], total=d.get("total", 0),
                    page=d.get("page", 1), page_size=d.get("pageSize", 15))

    # -- helpers ------------------------------------------------------------
    def _categories_map(self) -> dict:
        if self._cats is None:
            data = self._get("/api/catalog/categories/")
            self._cats = {cat["id"]: self._category(cat) for cat in data}
        return self._cats

    def _enrich_line_products(self, order: dtos.Order) -> dtos.Order:
        for line in order.lines:
            try:
                line.product = self.get_product(line.productId) or line.product
            except Exception:
                line.product = line.product
        return order

    # -- interface ----------------------------------------------------------
    def list_orders(self, *, status=None, delivery_type=None, payment_type=None, client_id=None,
                    search=None, date_from=None, date_to=None, page=1, page_size=15) -> Page:
        rows = [self._order(x) for x in self._get(
            "/api/orders/", status=status, delivery_type=delivery_type, payment_type=payment_type,
            search=search, date_from=date_from, date_to=date_to)]
        rows = [o for o in rows if o is not None]
        if client_id:
            rows = [o for o in rows if o.clientId == client_id]
        return _paginate_items(rows, page, page_size)

    def get_order(self, order_id):
        order = self._order(self._get(f"/api/orders/{order_id}/"))
        return self._enrich_line_products(order) if order else None

    def update_order_status(self, order_id, status):
        self._patch(f"/api/orders/{order_id}/status/", {"status": status})
        return self.get_order(order_id)

    def create_order(self, payload):
        body = {}
        if payload.get("client_id"):
            body["client_id"] = payload["client_id"]
        draft = self._post("/api/orders/draft/", body)
        order_id = draft["order_id"]

        for item in payload.get("lines", []):
            self._post(f"/api/orders/{order_id}/lines/", {
                "product_id": item["product_id"], "quantity": int(item["quantity"]),
            })

        delivery = payload.get("delivery_type")
        if delivery:
            delivery_body = {"delivery_type": delivery}
            if payload.get("address_id"):
                delivery_body["address_id"] = payload["address_id"]
            self._patch(f"/api/orders/{order_id}/delivery/", delivery_body)

        self._post(f"/api/orders/{order_id}/confirm/", {})
        return self.get_order(order_id)

    def all_orders(self):
        orders = [self._order(x) for x in self._get("/api/orders/all/")]
        return [o for o in orders if o is not None]

    def list_products(self, *, search=None, category_id=None, only_available=False, page=1, page_size=20):
        data = self._get("/api/catalog/products/", category_id=category_id,
                         available="true" if only_available else None)
        cats = self._categories_map()
        rows = []
        for raw in data:
            product = self._product(raw)
            if product is None:
                continue
            product.category = cats.get(product.categoryId)
            if search:
                needle = search.lower().strip()
                haystack = f"{product.name} {product.description}".lower()
                if needle not in haystack and not (
                    product.category and needle in product.category.description.lower()
                ):
                    continue
            rows.append(product)
        rows.sort(key=lambda p: p.description)
        return _paginate_items(rows, page, page_size)

    def get_product(self, product_id):
        return self._product(self._get(f"/api/catalog/products/{product_id}/"))

    def set_product_availability(self, product_id, available):
        return self._product(self._patch(f"/api/catalog/products/{product_id}/",
                                         {"available": bool(available)}))

    def save_product(self, payload):
        product_id = payload.get("id")
        if product_id:
            body = {"name": payload["name"], "description": payload["description"],
                    "category_id": payload["category_id"]}
            if payload.get("available") is not None:
                body["available"] = bool(payload["available"])
            self._patch(f"/api/catalog/products/{product_id}/", body)
            return self.get_product(product_id)
        created = self._post("/api/catalog/products/", {
            "name": payload["name"], "description": payload["description"], "category_id": payload["category_id"],
        })
        new_id = created["id"]
        if payload.get("available") is not None:
            self._patch(f"/api/catalog/products/{new_id}/", {"available": bool(payload["available"])})
        if payload.get("price"):
            self.add_product_price(new_id, payload["price"])
        return self.get_product(new_id)

    def add_product_price(self, product_id, price):
        self._post(f"/api/catalog/products/{product_id}/prices/", {
            "price": str(price), "since_date": date.today().isoformat(),
        })
        return self.get_product(product_id)

    def list_categories(self):
        return list(self._categories_map().values())

    def save_category(self, payload):
        if payload.get("id"):
            raise RuntimeError("Actualizar categorías aún no está soportado por el backend.")
        return self._category(self._post("/api/catalog/categories/",
                                         {"description": payload["description"]}))

    # -- payments (not in scope yet) ---------------------------------------
    def list_payments(self, *, status=None, provider=None, date_from=None, date_to=None, page=1, page_size=15):
        return _paginate_items([], page, page_size)

    def get_payment(self, payment_id):
        return None

    def all_payments(self):
        return []

    # -- clients (not in scope yet) ----------------------------------------
    def list_clients(self, *, search=None, page=1, page_size=15):
        return _paginate_items([], page, page_size)

    def get_client(self, client_id):
        return None

    def create_client(self, name, last_name, phone):
        raise NotImplementedError("El módulo de clientes no existe en el backend todavía.")

    def search_clients(self, query):
        return []

    # -- coupons (not in scope yet) ----------------------------------------
    def list_coupons(self):
        return []

    def get_coupon(self, coupon_id):
        return None

    def get_coupon_by_code(self, code):
        return None

    def save_coupon(self, payload):
        raise NotImplementedError("El módulo de cupones no existe en el backend todavía.")

    def validate_coupon(self, code, subtotal):
        return CouponValidation(valid=False,
                                reason="Módulo de cupones no disponible en el backend.")

    def list_applied_coupons(self, *, coupon_id=None):
        return []

    # -- conversations (not in scope yet) ----------------------------------
    def list_conversations(self):
        return []

    def get_conversation(self, conversation_id):
        return None

    # -- business configuration (not in scope yet) -------------------------
    def get_business_config(self):
        return dtos.BusinessConfiguration(
            id="", businessName="", minOrder=Decimal("0"), shippingCost=Decimal("0"),
            availableZone="", businessHours=[], addresses=[])

    def save_business_config(self, payload):
        raise NotImplementedError("El módulo de configuración no existe en el backend todavía.")