"""HttpRapidfoodClient — consumes the real backend API.

This is the production implementation: it maps each interface method to an HTTP
call against the backend that owns the domain/Prisma/PostgreSQL, and parses the
JSON responses back into the same DTOs the mock returns. It deliberately does NOT
reimplement any business rule — it only transports and maps.

Products, orders and clients are wired to the real catalog/order/client endpoints
(``api/catalog/*``, ``api/orders/*``, ``api/clients/*``) mapping their canonical
payloads into the UI DTOs. The remaining modules (coupons, payments,
conversations, business configuration) have no backend endpoints yet, so their
read methods return empty/neutral values to keep the panel navigable.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from . import dtos
from .client import CouponValidation, Page, RapidfoodClient


class ApiAuthError(RuntimeError):
    """The backend rejected the session token (auth failure).

    DRF returns 401 for AuthenticationFailed only when the authentication class
    exposes a challenge header; SupabaseJWTAuthentication does not, so an expired
    or invalid token comes back as 403. A 403 is treated as an auth failure only
    when its detail looks like a token/credential problem, so a genuine
    permission denial is not mistaken for a dead session.
    """

    status_code = 401


def _looks_like_auth_failure(status_code: int, detail: str) -> bool:
    if status_code == 401:
        return True
    if status_code != 403:
        return False
    text = (detail or "").lower()
    return any(
        marker in text
        for marker in ("token", "authentication", "credentials", "jwt", "authorization")
    )


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
        self._variants = None

    # -- transport helpers --------------------------------------------------
    def _get(self, path: str, **params) -> object:
        clean = {k: v for k, v in params.items() if v not in (None, "")}
        resp = self.session.get(f"{self.base_url}{path}", params=clean, timeout=15)
        self._raise_if_error(resp)
        return resp.json()

    def _post(self, path: str, payload: dict) -> object:
        resp = self.session.post(f"{self.base_url}{path}", json=payload, timeout=15)
        self._raise_if_error(resp)
        # 204 No Content won't have a JSON body
        if resp.status_code == 204:
            return None
        return resp.json()

    def _patch(self, path: str, payload: dict) -> object:
        resp = self.session.patch(f"{self.base_url}{path}", json=payload, timeout=15)
        self._raise_if_error(resp)
        return resp.json()

    def _put(self, path: str, payload: list | dict) -> object:
        resp = self.session.put(f"{self.base_url}{path}", json=payload, timeout=15)
        self._raise_if_error(resp)
        # 204 No Content won't have a JSON body
        if resp.status_code == 204:
            return None
        return resp.json()

    def _delete(self, path: str) -> None:
        resp = self.session.delete(f"{self.base_url}{path}", timeout=15)
        self._raise_if_error(resp)

    @staticmethod
    def _raise_if_error(resp) -> None:
        if resp.ok:
            return
        try:
            body = resp.json()
            message = body.get("detail") or body.get("error") or resp.text
        except Exception:
            message = resp.text
        if _looks_like_auth_failure(resp.status_code, message):
            raise ApiAuthError(message or "Session expired")
        raise RuntimeError(message)

    # -- mappers (JSON -> DTO) ---------------------------------------------

    def _price(self, d) -> Optional[dtos.Price]:
        if not d:
            return None
        return dtos.Price(id=d["id"], productId=d.get("product_id"),
                          price=_dec(d["price"]), sinceDate=_parse_dt(d["since_date"]))

    def _ingredient(self, d) -> Optional[dtos.Ingredient]:
        if not d:
            return None
        return dtos.Ingredient(id=d.get("ingredient_id", d.get("id")), name=d["name"])

    def _variant(self, d) -> Optional[dtos.Variant]:
        if not d:
            return None
        return dtos.Variant(id=d.get("variant_id", d.get("id")), name=d.get("variant_name", d.get("name")), 
                            available=d.get("is_available", d.get("available", True)),
                            currentPrice=_dec(d.get("price", d.get("current_price"))),
                            ingredients=[self._variant_ingredient(i) for i in d.get("ingredients", []) if i],
                            prices=sorted(
                                (self._variant_price(p) for p in d.get("prices", []) if p),
                                key=lambda p: p.sinceDate,
                                reverse=True,
                            ))

    def _variant_price(self, d) -> Optional[dtos.Price]:
        if not d:
            return None
        return dtos.Price(id=d["id"], productId=d.get("product_id", ""),
                          price=_dec(d["price"]), sinceDate=_parse_dt(d["since_date"]))

    def _variant_ingredient(self, d) -> Optional[dtos.VariantIngredient]:
        if not d:
            return None
        return dtos.VariantIngredient(
            id=d.get("id", ""),
            ingredientId=d.get("ingredient_id", d.get("id")),
            name=d.get("name", ""),
            removable=d.get("removable", True)
        )

    def _modifier_option(self, d) -> Optional[dtos.ModifierOption]:
        if not d:
            return None
        return dtos.ModifierOption(id=d.get("option_id", d.get("id")), name=d["name"], priceDelta=_dec(d.get("price_delta")),
                                   available=d.get("available", True))

    def _modifier_group(self, d) -> Optional[dtos.ModifierGroup]:
        if not d:
            return None
        return dtos.ModifierGroup(id=d.get("group_id", d.get("id")), name=d["name"], minSelections=d.get("min_selections", 0),
                                  maxSelections=d.get("max_selections", 1),
                                  options=[self._modifier_option(o) for o in d.get("options", []) if o])

    def _client(self, d) -> Optional[dtos.Client]:
        if not d:
            return None
        return dtos.Client(
            id=d.get("id", d.get("client_id")),
            name=d["name"],
            lastName=d.get("lastName", d.get("last_name", "")),
            phoneNumber=d.get("phoneNumber", d.get("phone_number", "")),
        )

    def _category(self, d) -> Optional[dtos.Category]:
        return None if not d else dtos.Category(id=d["id"], description=d["description"])

    def _product(self, d) -> Optional[dtos.Product]:
        if not d:
            return None
        state = d.get("state")
        available = d.get("available")
        if available is None:
            available = state == "available"
        return dtos.Product(id=d["id"], name=d["name"], description=d["description"], available=bool(available),
                            categoryId=d["category_id"], category=self._category(d.get("category")),
                            prices=[self._price(p) for p in d.get("prices", [])],
                            imageUrl=d.get("image_url") or None,
                            variants=[self._variant(v) for v in d.get("variants", []) if v],
                            modifierGroups=[self._modifier_group(g) for g in d.get("modifierGroups", []) if g])

    def _line(self, d) -> dtos.OrderLine:
        return dtos.OrderLine(id=d["id"], orderId=d["order_id"], productId=d.get("product_id"),
                              quantity=d["quantity"], subtotal=_dec(d["subtotal"]),
                              unitPrice=_dec(d.get("unit_price")), discountId=d.get("discount_id"),
                              product=self._product(d.get("product")),
                              productVariantId=d.get("product_variant_id"))

    def _applied_coupon(self, d) -> dtos.AppliedCoupon:
        return dtos.AppliedCoupon(
            id=d.get("id"),
            orderId=d.get("orderId", d.get("order_id")),
            couponId=d.get("couponId", d.get("coupon_id")),
            couponCode=d.get("couponCode", d.get("coupon_code")),
            type=d.get("type", d.get("coupon_type")),
            amount=_dec(d.get("amount")),
            discountAmount=_dec(d.get("discountAmount", d.get("discount_amount"))),
            availableUses=d.get("availableUses", d.get("available_uses")),
            dateOfExpiration=_parse_dt(d.get("dateOfExpiration", d.get("date_of_expiration"))),
            appliedAt=_parse_dt(d.get("appliedAt", d.get("applied_at"))),
        )

    def _payment(self, d) -> dtos.Payment:
        return dtos.Payment(id=d["id"], orderId=d["orderId"], provider=d["provider"],
                            status=d["status"], amount=_dec(d["amount"]), externalId=d.get("externalId"),
                            createdAt=_parse_dt(d["createdAt"]), updatedAt=_parse_dt(d["updatedAt"]))

    def _address(self, d) -> Optional[dtos.Address]:
        if not d:
            return None
        return dtos.Address(id=d["id"], street=d["street"], streetNumber=d.get("streetNumber", d.get("street_number")),
                            city=d["city"], province=d["province"], floor=d.get("floor"),
                            apartment=d.get("apartment"), postalCode=d.get("postalCode", d.get("postal_code")))

    def _business_hours(self, d) -> dtos.BusinessHours:
        return dtos.BusinessHours(id=d["id"], openWeekDay=d.get("openWeekDay", d.get("open_week_day")),
                                  openFromHour=d.get("openFromHour", d.get("open_from_hour")), openToHour=d.get("openToHour", d.get("open_to_hour")),
                                  businessConfigId=d.get("businessConfigId", d.get("business_config_id")))

    def _business_config(self, d) -> Optional[dtos.BusinessConfiguration]:
        if not d:
            return None
        return dtos.BusinessConfiguration(
            id=d["id"], businessName=d.get("businessName", d.get("business_name")), minOrder=_dec(d.get("minOrder", d.get("min_order"))),
            shippingCost=_dec(d.get("shippingCost", d.get("shipping_cost"))), availableZone="",
            businessHours=[self._business_hours(h) for h in d.get("businessHours", d.get("business_hours", []))],
            addresses=[self._address(a) for a in d.get("addresses", [])]
        )

    def _order(self, d) -> Optional[dtos.Order]:
        if not d:
            return None
        order = dtos.Order(
            id=d["id"], status=d["status"], origin=d.get("origin", "IN_PLACE"),
            subtotal=_dec(d["subtotal"]), discount=_dec(d["discount"]),
            createdAt=_parse_dt(d.get("created_at")), estimatedTime=d.get("estimated_time"),
            deliveryType=d.get("delivery_type"), paymentType=d.get("payment_type"),
            shippingCost=_dec(d.get("shipping_cost")), totalAmount=_dec(d.get("total_amount")),
            clientId=d.get("client_id"), clientName=d.get("client_name"), addressId=d.get("address_id"),
            conversationId=d.get("conversation_id"), appliedCouponId=d.get("applied_coupon_id"),
            confirmedAt=_parse_dt(d.get("confirmed_at")), client=self._client(d.get("client")),
            address=self._address(d.get("address")),
            lines=[self._line(x) for x in d.get("lines", [])],
            appliedCoupons=[self._applied_coupon(x) for x in d.get("appliedCoupons", [])],
            payments=[self._payment(x) for x in d.get("payments", [])])
        return self._map_line_products(order)

    def _coupon(self, d) -> Optional[dtos.Coupon]:
        if not d:
            return None
        return dtos.Coupon(
            id=d.get("coupon_id", d.get("id")),
            couponCode=d.get("coupon_code", d.get("couponCode")),
            type=d.get("coupon_type", d.get("type")),
            amount=_dec(d.get("amount")),
            availableUses=d.get("available_uses", d.get("availableUses")),
            minOrderAmount=_dec(d.get("min_order_amount", d.get("minOrderAmount"))),
            dateOfExpiration=_parse_dt(d.get("date_of_expiration", d.get("dateOfExpiration"))),
            isActive=d.get("is_active", d.get("isActive", True)),
        )

    def _message(self, d) -> dtos.Message:
        # The conversation API answers snake_case; keep camelCase tolerance.
        return dtos.Message(
            id=d.get("message_id", d.get("id")),
            conversationId=d.get("conversation_id", d.get("conversationId", "")),
            role=d.get("role"),
            author=d.get("author") or ("CLIENT" if d.get("role") == "USER" else "AGENT"),
            content=d.get("content", ""),
            detectedIntent=d.get("detected_intent", d.get("detectedIntent")),
            sentiment=d.get("sentiment"),
            status=d.get("status"),
            createdAt=_parse_dt(d.get("created_at", d.get("createdAt"))),
        )

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
        data = self._get("/api/catalog/categories/")
        return {cat["id"]: self._category(cat) for cat in data}

    def _variant_product_index(self) -> dict:
        if self._variants is None:
            index = {}
            try:
                for product in self.list_products(only_available=False, page_size=1000).items:
                    for variant in product.variants or []:
                        index[variant.id] = product
            except Exception:
                index = {}
            self._variants = index
        return self._variants

    def _map_line_products(self, order: dtos.Order) -> dtos.Order:
        """The order API exposes lines by variant id, so resolve each line's product."""
        pending = [line for line in order.lines if line.product is None and line.productVariantId]
        if not pending:
            return order
        index = self._variant_product_index()
        for line in pending:
            product = index.get(line.productVariantId)
            if product is not None:
                line.product = product
                line.productId = product.id
        return order

    def _enrich_line_products(self, order: dtos.Order) -> dtos.Order:
        return self._map_line_products(order)

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

    def cancel_order(self, order_id, reason=""):
        self._post(f"/api/orders/{order_id}/cancel/", {"reason": reason})
        return self.get_order(order_id)

    def create_order(self, payload):
        body = {}
        if payload.get("client_id"):
            body["client_id"] = payload["client_id"]
        if payload.get("client_name"):
            body["client_name"] = payload["client_name"]
        body["origin"] = payload.get("origin") or "IN_PLACE"
        draft = self._post("/api/orders/draft/", body)
        order_id = draft["order_id"]

        for item in payload.get("lines", []):
            line_payload = {
                "product_variant_id": item.get("product_variant_id") or item.get("product_id"),
                "quantity": int(item["quantity"]),
                "modifier_option_ids": item.get("modifier_option_ids", []),
                "removed_ingredient_ids": item.get("removed_ingredient_ids", [])
            }
            self._post(f"/api/orders/{order_id}/lines/", line_payload)

        delivery = payload.get("delivery_type")
        if delivery:
            delivery_body = {"delivery_type": delivery}
            if payload.get("address_id"):
                delivery_body["address_id"] = payload["address_id"]
            for key in ("street", "street_number", "floor", "apartment",
                        "city", "province", "postal_code"):
                if payload.get(key):
                    delivery_body[key] = payload[key]
            self._patch(f"/api/orders/{order_id}/delivery/", delivery_body)

        # The payment method is part of the snapshot being confirmed; the POS
        # always chooses one, so persist it before confirming.
        payment_type = payload.get("payment_type")
        if payment_type:
            self._patch(
                f"/api/orders/{order_id}/payment-type/",
                {"payment_type": payment_type},
            )

        if payload.get("coupon_code"):
            # Best-effort: a coupon that can't be applied must not block the order.
            try:
                self._post(f"/api/orders/{order_id}/coupon/", {"coupon_code": payload["coupon_code"]})
            except RuntimeError:
                pass

        self._post(f"/api/orders/{order_id}/confirm/", {})
        return self.get_order(order_id)

    def quote_delivery(self, business_config_id, address):
        body = {
            "destination_address": {
                "street": address["street"],
                "street_number": address["street_number"],
                "city": address["city"],
                "province": address["province"],
                "floor": address.get("floor") or None,
                "apartment": address.get("apartment") or None,
                "postal_code": address.get("postal_code") or None,
            }
        }
        return self._post(f"/api/delivery/{business_config_id}/quote/", body)

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

    def delete_product(self, product_id):
        self._delete(f"/api/catalog/products/{product_id}/")

    def save_product(self, payload):
        product_id = payload.get("id")
        if product_id:
            body = {"name": payload["name"], "description": payload["description"],
                    "category_id": payload["category_id"]}
            if payload.get("image_url") is not None:
                body["image_url"] = payload["image_url"]
            if payload.get("available") is not None:
                body["available"] = bool(payload["available"])
            self._patch(f"/api/catalog/products/{product_id}/", body)
            return self.get_product(product_id)
        created = self._post("/api/catalog/products/", {
            "name": payload["name"], "description": payload["description"],
            "category_id": payload["category_id"], "image_url": payload.get("image_url") or "",
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

    def list_ingredients(self):
        return [self._ingredient(x) for x in self._get("/api/catalog/ingredients/")]

    def create_ingredient(self, payload):
        return self._ingredient(self._post("/api/catalog/ingredients/", payload))

    def update_ingredient(self, ingredient_id, payload):
        return self._ingredient(self._patch(f"/api/catalog/ingredients/{ingredient_id}/", payload))

    def create_variant(self, product_id, payload):
        return self._variant(self._post(f"/api/catalog/products/{product_id}/variants/", payload))

    def update_variant(self, variant_id, payload):
        return self._variant(self._patch(f"/api/catalog/variants/{variant_id}/", payload))

    def set_variant_price(self, variant_id, price, since_date=None):
        self._post(f"/api/catalog/variants/{variant_id}/prices/", {
            "price": str(price), "since_date": (since_date or date.today()).isoformat(),
        })

    def set_variant_ingredients(self, variant_id, payload):
        return self._put(f"/api/catalog/variants/{variant_id}/ingredients/", payload)

    def create_modifier_group(self, product_id, payload):
        return self._modifier_group(self._post(f"/api/catalog/products/{product_id}/modifier-groups/", payload))

    def update_modifier_group(self, group_id, payload):
        return self._modifier_group(self._patch(f"/api/catalog/modifier-groups/{group_id}/", payload))

    def create_modifier_option(self, group_id, payload):
        return self._modifier_option(self._post(f"/api/catalog/modifier-groups/{group_id}/options/", payload))

    def update_modifier_option(self, option_id, payload):
        return self._modifier_option(self._patch(f"/api/catalog/modifier-options/{option_id}/", payload))

    def delete_modifier_group(self, group_id):
        self._delete(f"/api/catalog/modifier-groups/{group_id}/")

    def delete_modifier_option(self, option_id):
        self._delete(f"/api/catalog/modifier-options/{option_id}/")

    # -- payments (not in scope yet) ---------------------------------------
    def list_payments(self, *, status=None, provider=None, date_from=None, date_to=None, page=1, page_size=15):
        return _paginate_items([], page, page_size)

    def get_payment(self, payment_id):
        return None

    def all_payments(self):
        return []

    # -- clients ------------------------------------------------------------
    def list_clients(self, *, search=None, page=1, page_size=15):
        rows = [self._client(x) for x in self._get("/api/clients/", search=search)]
        rows = [c for c in rows if c is not None]
        rows.sort(key=lambda c: (c.name, c.lastName))
        return _paginate_items(rows, page, page_size)

    def get_client(self, client_id):
        return self._client(self._get(f"/api/clients/{client_id}/"))

    def delete_client(self, client_id):
        self._delete(f"/api/clients/{client_id}/")

    def create_client(self, name, last_name, phone):
        return self._client(self._post("/api/clients/create/", {
            "name": name, "last_name": last_name, "phone_number": phone,
        }))

    def search_clients(self, query):
        return self.list_clients(search=query, page=1, page_size=8).items

    def create_address(self, payload):
        client_id = payload.get("clientId") or payload.get("client_id")
        body = {
            "street": payload["street"],
            "street_number": payload.get("streetNumber", payload.get("street_number")),
            "city": payload["city"],
            "province": payload["province"],
            "floor": payload.get("floor"),
            "apartment": payload.get("apartment"),
            "postal_code": payload.get("postalCode", payload.get("postal_code")),
            "latitude": str(payload["latitude"]),
            "longitude": str(payload["longitude"]),
            "delivery_instructions": payload.get("deliveryInstructions"),
            "label": payload.get("label"),
            "is_default": bool(payload.get("isDefault", payload.get("is_default", False))),
        }
        return self._address(self._post(f"/api/clients/{client_id}/addresses/", body))

    # -- coupons -----------------------------------------------------------
    def list_coupons(self):
        rows = [self._coupon(x) for x in self._get("/api/coupons/list/")]
        return [c for c in rows if c is not None]

    def get_coupon(self, coupon_id):
        return next((c for c in self.list_coupons() if c.id == coupon_id), None)

    def get_coupon_by_code(self, code):
        try:
            return self._coupon(self._get(f"/api/coupons/by-code/{code}/"))
        except RuntimeError:
            return None

    def save_coupon(self, payload):
        expiration = payload.get("dateOfExpiration", payload.get("date_of_expiration"))
        body = {
            "coupon_code": payload.get("couponCode", payload.get("coupon_code")),
            "coupon_type": payload.get("type", payload.get("coupon_type")),
            "amount": str(payload.get("amount", 0)),
            "available_uses": payload.get("availableUses", payload.get("available_uses")),
            "min_order_amount": (str(payload["minOrderAmount"])
                                 if payload.get("minOrderAmount") is not None else None),
            "date_of_expiration": expiration.isoformat() if hasattr(expiration, "isoformat") else expiration,
            "is_active": payload.get("isActive", payload.get("is_active", True)),
        }
        return self._coupon(self._post("/api/coupons/", body))

    def update_coupon(self, coupon_id, payload):
        expiration = payload.get("dateOfExpiration", payload.get("date_of_expiration"))
        body = {
            "amount": str(payload.get("amount", 0)),
            "available_uses": payload.get("availableUses", payload.get("available_uses")),
            "min_order_amount": (str(payload["minOrderAmount"])
                                 if payload.get("minOrderAmount") is not None else None),
            "date_of_expiration": expiration.isoformat() if hasattr(expiration, "isoformat") else expiration,
            "is_active": payload.get("isActive", payload.get("is_active", True)),
        }
        return self._coupon(self._patch(f"/api/coupons/{coupon_id}/", body))

    def set_coupon_active(self, coupon_id, is_active):
        self._patch(f"/api/coupons/{coupon_id}/status/", {"is_active": bool(is_active)})

    def validate_coupon(self, code, subtotal):
        try:
            data = self._post("/api/coupons/validate/", {
                "coupon_code": code, "subtotal": str(subtotal),
            })
        except RuntimeError as exc:
            return CouponValidation(valid=False, reason=str(exc))
        if not data.get("valid"):
            return CouponValidation(valid=False, reason=data.get("reason", "Cupón inválido."))
        return CouponValidation(valid=True, discount_amount=_dec(data.get("discount_amount")),
                                coupon=self._coupon(data))

    def list_applied_coupons(self, *, coupon_id=None):
        if not coupon_id:
            return []
        rows = self._get("/api/orders/applied-coupons/", coupon_id=coupon_id)
        return [self._applied_coupon(x) for x in rows if x]

    # -- conversations ------------------------------------------------------
    def list_conversations(self):
        rows = self._get("/api/conversation/")
        result = []
        for d in rows:
            last = d.get("last_message")
            result.append(
                dtos.Conversation(
                    id=d["id"],
                    channel=d.get("channel", ""),
                    clientId=d.get("client_id"),
                    agentPaused=bool(d.get("agent_paused")),
                    externalThreadId=d.get("external_thread_id"),
                    clientName=d.get("client_name"),
                    clientPhone=d.get("client_phone"),
                    messageCount=int(d.get("message_count") or 0),
                    lastMessage=last,
                    lastAt=_parse_dt(d.get("last_at")),
                )
            )
        return result

    def get_conversation(self, conversation_id):
        return self._conversation_detail(
            self._get(f"/api/conversation/{conversation_id}/messages/")
        )

    def send_client_message(self, conversation_id, content):
        return self._conversation_detail(
            self._post(f"/api/conversation/{conversation_id}/client-message/", {"content": content})
        )

    def send_operator_message(self, conversation_id, content):
        return self._conversation_detail(
            self._post(f"/api/conversation/{conversation_id}/operator-message/", {"content": content})
        )

    def set_conversation_takeover(self, conversation_id, paused):
        action = "takeover" if paused else "release"
        return self._conversation_detail(
            self._post(f"/api/conversation/{conversation_id}/{action}/", {})
        )

    def _conversation_detail(self, d) -> Optional[dtos.Conversation]:
        if not d:
            return None
        return dtos.Conversation(
            id=d["conversation_id"],
            channel=d.get("channel", ""),
            clientId=d.get("client_id"),
            agentPaused=bool(d.get("agent_paused")),
            externalThreadId=d.get("external_thread_id"),
            clientName=d.get("client_name"),
            clientPhone=d.get("client_phone"),
            lastIntent=d.get("last_intent"),
            overallSentiment=d.get("overall_sentiment"),
            messages=[self._message(m) for m in d.get("messages", [])],
            messageCount=len(d.get("messages", [])),
        )

    # -- business configuration --------------------------------------------
    def get_business_config(self):
        try:
            raw = self._get("/api/business/default/")
            return self._business_config(raw)
        except RuntimeError:
            return dtos.BusinessConfiguration(
                id="default", businessName="", minOrder=Decimal("0"), shippingCost=Decimal("0"),
                availableZone="", businessHours=[], addresses=[])

    def save_business_config(self, payload):
        # Map camelCase from UI payload to snake_case for API
        body = {
            "business_name": payload.get("businessName", ""),
            "min_order": str(payload.get("minOrder", 0)),
            "shipping_cost": str(payload.get("shippingCost", 0)),
        }
        self._patch("/api/business/default/", body)
        return self.get_business_config()

    def save_business_hours(self, business_config_id: str, hours: list) -> None:
        payload = [
            {
                "open_week_day": h.get("open_week_day", h.get("openWeekDay")),
                "open_from_hour": h.get("open_from_hour", h.get("openFromHour")),
                "open_to_hour": h.get("open_to_hour", h.get("openToHour"))
            }
            for h in hours
        ]
        self._put(f"/api/business/{business_config_id}/hours/", payload)

    def create_business_address(self, business_config_id: str, payload: dict) -> dtos.Address:
        body = {
            "street": payload["street"],
            "street_number": payload["streetNumber"],
            "city": payload["city"],
            "province": payload["province"],
            "floor": payload.get("floor"),
            "apartment": payload.get("apartment"),
            "postal_code": payload.get("postalCode")
        }
        res = self._post(f"/api/business/{business_config_id}/addresses/", body)
        return self._address(res)

    def update_business_address(self, business_config_id: str, address_id: str, payload: dict) -> dtos.Address:
        body = {
            "street": payload["street"],
            "street_number": payload["streetNumber"],
            "city": payload["city"],
            "province": payload["province"],
            "floor": payload.get("floor"),
            "apartment": payload.get("apartment"),
            "postal_code": payload.get("postalCode")
        }
        res = self._patch(f"/api/business/{business_config_id}/addresses/{address_id}/", body)
        return self._address(res)

    def delete_business_address(self, business_config_id: str, address_id: str) -> None:
        self._delete(f"/api/business/{business_config_id}/addresses/{address_id}/")

    # -- delivery configuration --------------------------------------------
    def get_delivery_config(self, business_config_id):
        try:
            return self._get(f"/api/delivery/{business_config_id}/configure/")
        except RuntimeError:
            return None

    def save_delivery_config(self, business_config_id, payload):
        return self._post(f"/api/delivery/{business_config_id}/configure/", payload)

    # -- Mercado Pago linking ----------------------------------------------
    def get_mercadopago_status(self):
        business_config_id = self.get_business_config().id
        return self._get("/api/mercadopago/status/", business_config_id=business_config_id)

    def get_mercadopago_authorization_url(self, business_config_id):
        payload = self._post("/api/mercadopago/authorize/",
                             {"business_config_id": business_config_id})
        return payload["authorization_url"]

    def unlink_mercadopago(self, business_config_id):
        self._post("/api/mercadopago/unlink/", {"business_config_id": business_config_id})

    def get_preparation_time_config(self, business_config_id):
        try:
            return self._get(
                f"/api/orders/preparation-time/{business_config_id}/configure/"
            )
        except RuntimeError:
            return None

    def save_preparation_time_config(self, business_config_id, payload):
        return self._post(
            f"/api/orders/preparation-time/{business_config_id}/configure/", payload
        )

    # -- WhatsApp configuration --------------------------------------------
    def get_whatsapp_config(self, business_config_id):
        try:
            return self._get(
                "/api/conversation/whatsapp/config/",
                business_config_id=business_config_id,
            )
        except RuntimeError:
            return {"configured": False}

    def save_whatsapp_config(self, business_config_id, payload):
        body = {**payload, "business_config_id": business_config_id}
        return self._put("/api/conversation/whatsapp/config/", body)
