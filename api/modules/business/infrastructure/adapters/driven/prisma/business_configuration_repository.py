"""Prisma-backed repository for BusinessConfiguration."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from shared.infrastructure.prisma.db import db

from modules.business.application.ports.driven.business_repository_port import (
    BusinessConfigurationRepositoryPort,
)
from modules.business.domain.models.business_configuration import (
    Address,
    BusinessConfiguration,
    BusinessHours,
)


import uuid

class PrismaBusinessConfigurationRepository(BusinessConfigurationRepositoryPort):

    def _resolve_id(self, business_config_id: str) -> Optional[str]:
        if business_config_id != "default":
            return business_config_id
        record = db.client.businessconfiguration.find_first()
        if record:
            return record.id
        return None

    def get_by_id(self, business_config_id: str) -> Optional[BusinessConfiguration]:
        real_id = self._resolve_id(business_config_id)
        if not real_id:
            return None
        record = db.client.businessconfiguration.find_unique(
            where={"id": real_id},
            include={"businessHours": True, "addresses": True},
        )
        if record is None:
            return None
        return self._to_domain(record)

    def save_general(
        self,
        business_config_id: str,
        *,
        business_name: str,
        min_order: object,
        shipping_cost: object,
    ) -> BusinessConfiguration:
        real_id = self._resolve_id(business_config_id)
        if not real_id:
            real_id = str(uuid.uuid4())

        data_dict = {
            "businessName": business_name,
            "minOrder": str(min_order),
            "shippingCost": str(shipping_cost),
        }
        record = db.client.businessconfiguration.upsert(
            where={"id": real_id},
            data={
                "create": {**data_dict, "id": real_id},
                "update": data_dict,
            },
            include={"businessHours": True, "addresses": True},
        )
        return self._to_domain(record)

    def replace_business_hours(
        self,
        business_config_id: str,
        hours: list[BusinessHours],
    ) -> None:
        real_id = self._resolve_id(business_config_id)
        if not real_id:
            raise ValueError(f"Business configuration not found for id {business_config_id}")

        # Delete all existing hours for this business
        db.client.businesshours.delete_many(
            where={"businessConfigId": real_id}
        )
        # Insert new ones
        for h in hours:
            db.client.businesshours.create(
                data={
                    "openWeekDay": h.openWeekDay,
                    "openFromHour": h.openFromHour,
                    "openToHour": h.openToHour,
                    "businessConfigId": real_id,
                }
            )

    def create_address(
        self,
        business_config_id: str,
        *,
        street: str,
        street_number: str,
        city: str,
        province: str,
        floor: Optional[str],
        apartment: Optional[str],
        postal_code: Optional[str],
    ) -> Address:
        real_id = self._resolve_id(business_config_id)
        if not real_id:
            raise ValueError(f"Business configuration not found for id {business_config_id}")

        record = db.client.address.create(
            data={
                "street": street,
                "streetNumber": street_number,
                "city": city,
                "province": province,
                "floor": floor,
                "apartment": apartment,
                "postalCode": postal_code,
                "businessConfigId": real_id,
            }
        )
        return self._address_to_domain(record)

    def update_address(
        self,
        address_id: str,
        *,
        street: str,
        street_number: str,
        city: str,
        province: str,
        floor: Optional[str],
        apartment: Optional[str],
        postal_code: Optional[str],
    ) -> Address:
        record = db.client.address.update(
            where={"id": address_id},
            data={
                "street": street,
                "streetNumber": street_number,
                "city": city,
                "province": province,
                "floor": floor,
                "apartment": apartment,
                "postalCode": postal_code,
            }
        )
        return self._address_to_domain(record)

    def delete_address(self, address_id: str) -> None:
        db.client.address.delete(where={"id": address_id})

    def get_address_by_id(self, address_id: str) -> Optional[Address]:
        record = db.client.address.find_unique(where={"id": address_id})
        if record is None:
            return None
        return self._address_to_domain(record)

    # ---- Mappers ----

    @staticmethod
    def _to_domain(record) -> BusinessConfiguration:
        hours = [
            PrismaBusinessConfigurationRepository._hours_to_domain(h)
            for h in (record.businessHours or [])
        ]
        # Sort hours by canonical weekday order
        _ORDER = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
        hours.sort(key=lambda h: _ORDER.index(h.openWeekDay) if h.openWeekDay in _ORDER else 99)

        addresses = [
            PrismaBusinessConfigurationRepository._address_to_domain(a)
            for a in (record.addresses or [])
        ]
        return BusinessConfiguration(
            id=record.id,
            businessName=record.businessName,
            minOrder=Decimal(str(record.minOrder)),
            shippingCost=Decimal(str(record.shippingCost)),
            businessHours=hours,
            addresses=addresses,
        )

    @staticmethod
    def _hours_to_domain(record) -> BusinessHours:
        return BusinessHours(
            id=record.id,
            openWeekDay=record.openWeekDay.value if hasattr(record.openWeekDay, "value") else str(record.openWeekDay),
            openFromHour=record.openFromHour,
            openToHour=record.openToHour,
            businessConfigId=record.businessConfigId,
        )

    @staticmethod
    def _address_to_domain(record) -> Address:
        return Address(
            id=record.id,
            street=record.street,
            streetNumber=record.streetNumber,
            city=record.city,
            province=record.province,
            businessConfigId=record.businessConfigId,
            floor=record.floor,
            apartment=record.apartment,
            postalCode=record.postalCode,
        )
