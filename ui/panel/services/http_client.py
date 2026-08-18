"""HttpRapidfoodClient — consumes the EXISTING backend API.

This is the production implementation: it maps each interface method to an HTTP
call against the backend that owns the domain/Prisma/PostgreSQL, and parses the
JSON responses back into the same DTOs the mock returns. It deliberately does NOT
reimplement any business rule — it only transports and maps.

It is a working skeleton: wire the concrete endpoint paths to match the real API
contract. Selecting it (RAPIDFOOD_CLIENT=http) must not require any change to
views or templates.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from . import dtos
from .client import CouponValidation, Page, RapidfoodClient


def _parse_dt(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _dec(value):
    return None if value is None else Decimal(str(value))


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

    # -- transport helpers --------------------------------------------------
    def _get(self, path: str, **params) -> object:
        clean = {k: v for k, v in params.items() if v not in (None, "")}
        resp = self.session.get(f"{self.base_url}{path}", params=clean, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, payload: dict) -> object:
        resp = self.session.post(f"{self.base_url}{path}", json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def _patch(self, path: str, payload: dict) -> object:
        resp = self.session.patch(f"{self.base_url}{path}", json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()

    # -- mappers (JSON -> DTO) ---------------------------------------------
    def _client(self, d) -> Optional[dtos.Client]:
        if not d:
            return None
        return dtos.Client(id=d["id"], name=d["name"], lastName=d["lastName"],
                           phoneNumber=d["phoneNumber"])

    def _category(self, d) -> Optional[dtos.Category]:
        return None if not d else dtos.Category(id=d["id"], description=d["description"])

    def _price(self, d) -> dtos.Price:
        return dtos.Price(id=d["id"], productId=d["productId"],
                          sinceDate=_parse_dt(d["sinceDate"]), price=_dec(d["price"]))

    def _product(self, d) -> Optional[dtos.Product]:
        if not d:
            return None
        return dtos.Product(id=d["id"], description=d["description"], available=d["available"],
                            categoryId=d["categoryId"], category=self._category(d.get("category")),
                            prices=[self._price(p) for p in d.get("prices", [])])

    def _line(self, d) -> dtos.OrderLine:
        return dtos.OrderLine(id=d["id"], orderId=d["orderId"], productId=d["productId"],
                              quantity=d["quantity"], subtotal=_dec(d["subtotal"]),
                              unitPrice=_dec(d.get("unitPrice")), discountId=d.get("discountId"),
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
            createdAt=_parse_dt(d["createdAt"]), estimatedTime=d.get("estimatedTime"),
            deliveryType=d.get("deliveryType"), paymentType=d.get("paymentType"),
            shippingCost=_dec(d.get("shippingCost")), totalAmount=_dec(d.get("totalAmount")),
            clientId=d.get("clientId"), addressId=d.get("addressId"),
            conversationId=d.get("conversationId"), appliedCouponId=d.get("appliedCouponId"),
            confirmedAt=_parse_dt(d.get("confirmedAt")), client=self._client(d.get("client")),
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

    def _business(self, d) -> dtos.BusinessConfiguration:
        return dtos.BusinessConfiguration(
            id=d["id"], businessName=d["businessName"], minOrder=_dec(d["minOrder"]),
            shippingCost=_dec(d["shippingCost"]), availableZone=d["availableZone"],
            businessHours=[dtos.BusinessHours(id=h["id"], openWeekDay=h["openWeekDay"],
                           openFromHour=h["openFromHour"], openToHour=h["openToHour"])
                           for h in d.get("businessHours", [])],
            addresses=[self._address(a) for a in d.get("addresses", [])])

    def _page(self, d, mapper) -> Page:
        return Page(items=[mapper(x) for x in d.get("items", [])], total=d.get("total", 0),
                    page=d.get("page", 1), page_size=d.get("pageSize", 15))

    # -- interface ----------------------------------------------------------
    def list_orders(self, *, status=None, delivery_type=None, payment_type=None, client_id=None,
                    search=None, date_from=None, date_to=None, page=1, page_size=15) -> Page:
        return self._page(self._get("/orders", status=status, deliveryType=delivery_type,
                          paymentType=payment_type, clientId=client_id, search=search,
                          dateFrom=date_from, dateTo=date_to, page=page, pageSize=page_size), self._order)

    def get_order(self, order_id): return self._order(self._get(f"/orders/{order_id}"))

    def update_order_status(self, order_id, status):
        return self._order(self._patch(f"/orders/{order_id}", {"status": status}))

    def create_order(self, payload): return self._order(self._post("/orders", payload))

    def all_orders(self): return [self._order(x) for x in self._get("/orders/all")]

    def list_products(self, *, search=None, category_id=None, only_available=False, page=1, page_size=20):
        return self._page(self._get("/products", search=search, categoryId=category_id,
                          onlyAvailable=only_available, page=page, pageSize=page_size), self._product)

    def get_product(self, product_id): return self._product(self._get(f"/products/{product_id}"))

    def set_product_availability(self, product_id, available):
        return self._product(self._patch(f"/products/{product_id}", {"available": available}))

    def save_product(self, payload):
        if payload.get("id"):
            return self._product(self._patch(f"/products/{payload['id']}", payload))
        return self._product(self._post("/products", payload))

    def add_product_price(self, product_id, price):
        return self._product(self._post(f"/products/{product_id}/prices", {"price": str(price)}))

    def list_categories(self): return [self._category(x) for x in self._get("/categories")]

    def save_category(self, payload):
        if payload.get("id"):
            return self._category(self._patch(f"/categories/{payload['id']}", payload))
        return self._category(self._post("/categories", payload))

    def list_payments(self, *, status=None, provider=None, date_from=None, date_to=None, page=1, page_size=15):
        return self._page(self._get("/payments", status=status, provider=provider, dateFrom=date_from,
                          dateTo=date_to, page=page, pageSize=page_size), self._payment)

    def get_payment(self, payment_id): return self._payment(self._get(f"/payments/{payment_id}"))

    def all_payments(self): return [self._payment(x) for x in self._get("/payments/all")]

    def list_clients(self, *, search=None, page=1, page_size=15):
        return self._page(self._get("/clients", search=search, page=page, pageSize=page_size), self._client)

    def get_client(self, client_id): return self._client(self._get(f"/clients/{client_id}"))

    def create_client(self, name, last_name, phone):
        return self._client(self._post("/clients", {"name": name, "lastName": last_name, "phoneNumber": phone}))

    def search_clients(self, query): return [self._client(x) for x in self._get("/clients/search", q=query)]

    def list_coupons(self): return [self._coupon(x) for x in self._get("/coupons")]

    def get_coupon(self, coupon_id): return self._coupon(self._get(f"/coupons/{coupon_id}"))

    def get_coupon_by_code(self, code): return self._coupon(self._get("/coupons/by-code", code=code))

    def save_coupon(self, payload):
        if payload.get("id"):
            return self._coupon(self._patch(f"/coupons/{payload['id']}", payload))
        return self._coupon(self._post("/coupons", payload))

    def validate_coupon(self, code, subtotal):
        d = self._post("/coupons/validate", {"code": code, "subtotal": str(subtotal)})
        return CouponValidation(valid=d["valid"], reason=d.get("reason", ""),
                                coupon=self._coupon(d.get("coupon")),
                                discount_amount=_dec(d.get("discountAmount")))

    def list_applied_coupons(self, *, coupon_id=None):
        return [self._applied_coupon(x) for x in self._get("/applied-coupons", couponId=coupon_id)]

    def list_conversations(self): return [self._conversation(x) for x in self._get("/conversations")]

    def get_conversation(self, conversation_id):
        return self._conversation(self._get(f"/conversations/{conversation_id}"))

    def get_business_config(self): return self._business(self._get("/business-configuration"))

    def save_business_config(self, payload):
        return self._business(self._patch("/business-configuration", payload))
