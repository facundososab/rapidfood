"""Data Transfer Objects mirroring the Prisma schema EXACTLY.

These are plain dataclasses (NOT Django models). They are the contract shared by
every RapidfoodClient implementation, so views/templates never depend on whether
data comes from the in-memory mock or the real HTTP backend.

Source of truth: src/imports/pasted_text/schema.txt. Do not add fields that do not
exist in the schema.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    PAID = "PAID"
    CONFIRMED = "CONFIRMED"
    IN_PREPARATION = "IN_PREPARATION"
    READY = "READY"
    DELIVERED = "DELIVERED"
    PICKED_UP = "PICKED_UP"
    CANCELLED = "CANCELLED"


class DeliveryType(str, Enum):
    DELIVERY = "DELIVERY"
    PICKUP = "PICKUP"


class PaymentType(str, Enum):
    CASH = "CASH"
    ONLINE = "ONLINE"


class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class WeekDay(str, Enum):
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


# Spanish labels for the enums (values stay canonical).
ORDER_STATUS_LABELS = {
    "DRAFT": "Borrador",
    "PENDING": "Pendiente",
    "PAID": "Pagado",
    "CONFIRMED": "Confirmado",
    "IN_PREPARATION": "En preparación",
    "READY": "Listo",
    "DELIVERED": "Entregado",
    "PICKED_UP": "Retirado",
    "CANCELLED": "Cancelado",
}
DELIVERY_TYPE_LABELS = {"DELIVERY": "Envío", "PICKUP": "Retiro"}
PAYMENT_TYPE_LABELS = {"CASH": "Efectivo", "ONLINE": "Online"}
PAYMENT_STATUS_LABELS = {
    "PENDING": "Pendiente",
    "APPROVED": "Aprobado",
    "REJECTED": "Rechazado",
    "FAILED": "Fallido",
    "EXPIRED": "Expirado",
}
WEEKDAY_LABELS = {
    "MONDAY": "Lunes",
    "TUESDAY": "Martes",
    "WEDNESDAY": "Miércoles",
    "THURSDAY": "Jueves",
    "FRIDAY": "Viernes",
    "SATURDAY": "Sábado",
    "SUNDAY": "Domingo",
}
WEEKDAY_ORDER = list(WEEKDAY_LABELS.keys())


@dataclass
class Category:
    id: str
    description: str


@dataclass
class Price:
    id: str
    productId: str
    sinceDate: datetime
    price: Decimal


@dataclass
class Product:
    id: str
    name: str
    description: str
    available: bool
    categoryId: str
    prices: List[Price] = field(default_factory=list)
    # convenience (resolved by the client, not a schema field)
    category: Optional[Category] = None
    # optional; schema Product.imageUrl
    imageUrl: Optional[str] = None


@dataclass
class Discount:
    id: str
    percentage: Decimal  # 0-100


@dataclass
class Client:
    id: str
    name: str
    lastName: str
    phoneNumber: str


@dataclass
class Address:
    id: str
    street: str
    streetNumber: str
    city: str
    province: str
    floor: Optional[str] = None
    apartment: Optional[str] = None
    postalCode: Optional[str] = None
    businessConfigId: Optional[str] = None


@dataclass
class OrderLine:
    id: str
    orderId: str
    productId: str
    quantity: int
    subtotal: Decimal
    unitPrice: Optional[Decimal] = None  # NULL in DRAFT, frozen at confirm
    discountId: Optional[str] = None
    # resolved conveniences
    product: Optional[Product] = None
    discount: Optional[Discount] = None


@dataclass
class AppliedCoupon:
    id: str
    orderId: str
    couponCode: str  # full snapshot, survives coupon deletion
    type: str
    amount: Decimal
    discountAmount: Decimal
    availableUses: int
    appliedAt: datetime
    couponId: Optional[str] = None
    dateOfExpiration: Optional[datetime] = None


@dataclass
class Payment:
    id: str
    orderId: str
    provider: str
    status: str  # PaymentStatus value
    amount: Decimal
    createdAt: datetime
    updatedAt: datetime
    externalId: Optional[str] = None


@dataclass
class Order:
    id: str
    status: str  # OrderStatus value
    subtotal: Decimal
    discount: Decimal
    createdAt: datetime
    estimatedTime: Optional[int] = None  # minutes
    deliveryType: Optional[str] = None
    paymentType: Optional[str] = None
    shippingCost: Optional[Decimal] = None
    totalAmount: Optional[Decimal] = None
    clientId: Optional[str] = None
    addressId: Optional[str] = None
    conversationId: Optional[str] = None
    appliedCouponId: Optional[str] = None
    confirmedAt: Optional[datetime] = None
    # resolved conveniences
    client: Optional[Client] = None
    address: Optional[Address] = None
    lines: List[OrderLine] = field(default_factory=list)
    appliedCoupons: List[AppliedCoupon] = field(default_factory=list)
    payments: List[Payment] = field(default_factory=list)


@dataclass
class Message:
    id: str
    conversationId: str
    role: str  # USER | AGENT | SYSTEM | open vocab
    content: str
    createdAt: datetime
    detectedIntent: Optional[str] = None
    sentiment: Optional[str] = None
    status: Optional[str] = None


@dataclass
class Conversation:
    id: str
    channel: str
    overallSentiment: Optional[str] = None
    lastIntent: Optional[str] = None
    clientId: Optional[str] = None
    # resolved conveniences
    client: Optional[Client] = None
    messages: List[Message] = field(default_factory=list)
    orders: List[Order] = field(default_factory=list)


@dataclass
class Coupon:
    id: str
    couponCode: str
    type: str  # FIXED_AMOUNT | PERCENTAGE | ... open vocab
    amount: Decimal
    availableUses: int
    dateOfExpiration: Optional[datetime] = None


@dataclass
class BusinessHours:
    id: str
    openWeekDay: str
    openFromHour: str  # "HH:MM"
    openToHour: str  # "HH:MM"
    businessConfigId: Optional[str] = None


@dataclass
class BusinessConfiguration:
    id: str
    businessName: str
    minOrder: Decimal
    shippingCost: Decimal
    availableZone: str
    businessHours: List[BusinessHours] = field(default_factory=list)
    addresses: List[Address] = field(default_factory=list)
