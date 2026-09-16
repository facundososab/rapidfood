def _serialize_config(config) -> dict:
    return {
        "id": config.id,
        "businessName": config.businessName,
        "minOrder": str(config.minOrder),
        "shippingCost": str(config.shippingCost),
        "businessHours": [
            {
                "id": h.id,
                "openWeekDay": h.openWeekDay,
                "openFromHour": h.openFromHour,
                "openToHour": h.openToHour,
            }
            for h in config.businessHours
        ],
        "addresses": [
            {
                "id": a.id,
                "street": a.street,
                "streetNumber": a.streetNumber,
                "city": a.city,
                "province": a.province,
                "floor": a.floor,
                "apartment": a.apartment,
                "postalCode": a.postalCode,
                "label": a.full_label(),
            }
            for a in config.addresses
        ],
    }
