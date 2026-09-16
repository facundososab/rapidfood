import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from prisma import Prisma


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def money(value: str | int | float) -> Decimal:
    return Decimal(str(value))


# -----------------------------------------------------------------------------
# Catalog data
# -----------------------------------------------------------------------------
# ProductVariantIngredient = ingredients INCLUDED in a concrete variant.
# ModifierGroup / ModifierOption = optional/required choices offered for Product.
#
# That distinction is intentional: e.g. "Tomate" can be an included/removable
# ingredient, while "Panceta extra" is a modifier selected by the customer.

PRODUCTS: list[dict[str, Any]] = [
    # -------------------------------------------------------------------------
    # HAMBURGUESAS
    # -------------------------------------------------------------------------
    {
        "name": "Classic Burger",
        "description": "Smash burger con cheddar, lechuga, tomate, cebolla morada y salsa de la casa en pan brioche.",
        "category": "Hamburguesas",
        "variants": [
            {
                "name": "Simple",
                "price": "7900.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Medallón de carne 120 g", False),
                    ("Queso cheddar", True),
                    ("Lechuga", True),
                    ("Tomate", True),
                    ("Cebolla morada", True),
                    ("Salsa de la casa", True),
                ],
            },
            {
                "name": "Doble",
                "price": "9500.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Medallón de carne 120 g", False),
                    ("Queso cheddar", True),
                    ("Lechuga", True),
                    ("Tomate", True),
                    ("Cebolla morada", True),
                    ("Salsa de la casa", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 5,
                "options": [
                    ("Medallón de carne extra", "2200.00"),
                    ("Cheddar extra", "900.00"),
                    ("Panceta crocante", "1300.00"),
                    ("Huevo a la plancha", "900.00"),
                    ("Cebolla caramelizada", "800.00"),
                ],
            },
            {
                "name": "Salsas extra",
                "min": 0,
                "max": 3,
                "options": [
                    ("Ketchup", "0.00"),
                    ("Mayonesa", "0.00"),
                    ("Mostaza", "0.00"),
                    ("Alioli", "450.00"),
                    ("Barbacoa", "450.00"),
                    ("Salsa picante", "450.00"),
                ],
            },
        ],
    },
    {
        "name": "Cheese Burger",
        "description": "Smash burger de carne con abundante queso cheddar y salsa especial en pan brioche.",
        "category": "Hamburguesas",
        "variants": [
            {
                "name": "Simple",
                "price": "7200.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Medallón de carne 120 g", False),
                    ("Queso cheddar", True),
                    ("Salsa especial", True),
                ],
            },
            {
                "name": "Doble",
                "price": "8800.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Medallón de carne 120 g", False),
                    ("Queso cheddar", True),
                    ("Salsa especial", True),
                ],
            },
            {
                "name": "Triple",
                "price": "10400.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Medallón de carne 120 g", False),
                    ("Queso cheddar", True),
                    ("Salsa especial", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 4,
                "options": [
                    ("Medallón de carne extra", "2200.00"),
                    ("Cheddar extra", "900.00"),
                    ("Panceta crocante", "1300.00"),
                    ("Pepinillos", "500.00"),
                    ("Cebolla caramelizada", "800.00"),
                ],
            },
            {
                "name": "Salsas extra",
                "min": 0,
                "max": 2,
                "options": [
                    ("Ketchup", "0.00"),
                    ("Mostaza", "0.00"),
                    ("Barbacoa", "450.00"),
                    ("Salsa picante", "450.00"),
                ],
            },
        ],
    },
    {
        "name": "Bacon BBQ Burger",
        "description": "Smash burger con cheddar, panceta crocante, cebolla caramelizada y salsa barbacoa.",
        "category": "Hamburguesas",
        "variants": [
            {
                "name": "Simple",
                "price": "8600.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Medallón de carne 120 g", False),
                    ("Queso cheddar", True),
                    ("Panceta", True),
                    ("Cebolla caramelizada", True),
                    ("Salsa BBQ", True),
                ],
            },
            {
                "name": "Doble",
                "price": "10200.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Medallón de carne 120 g", False),
                    ("Queso cheddar", True),
                    ("Panceta", True),
                    ("Cebolla caramelizada", True),
                    ("Salsa BBQ", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 5,
                "options": [
                    ("Medallón de carne extra", "2200.00"),
                    ("Cheddar extra", "900.00"),
                    ("Panceta extra", "1300.00"),
                    ("Huevo a la plancha", "900.00"),
                    ("Cebolla caramelizada extra", "800.00"),
                ],
            },
            {
                "name": "Salsas extra",
                "min": 0,
                "max": 2,
                "options": [
                    ("BBQ extra", "450.00"),
                    ("Alioli", "450.00"),
                    ("Salsa picante", "450.00"),
                ],
            },
        ],
    },
    {
        "name": "Oklahoma Onion Burger",
        "description": "Smash burger prensada con cebolla, cheddar, pepinillos y mostaza en pan brioche.",
        "category": "Hamburguesas",
        "variants": [
            {
                "name": "Simple",
                "price": "8100.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Medallón de carne 120 g", False),
                    ("Queso cheddar", True),
                    ("Cebolla", True),
                    ("Pepinillos", True),
                    ("Mostaza", True),
                ],
            },
            {
                "name": "Doble",
                "price": "9700.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Medallón de carne 120 g", False),
                    ("Queso cheddar", True),
                    ("Cebolla", True),
                    ("Pepinillos", True),
                    ("Mostaza", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 4,
                "options": [
                    ("Medallón de carne extra", "2200.00"),
                    ("Cheddar extra", "900.00"),
                    ("Panceta crocante", "1300.00"),
                    ("Pepinillos extra", "500.00"),
                ],
            },
            {
                "name": "Salsas extra",
                "min": 0,
                "max": 2,
                "options": [
                    ("Mostaza extra", "0.00"),
                    ("Ketchup", "0.00"),
                    ("Salsa especial", "450.00"),
                ],
            },
        ],
    },
    {
        "name": "Crispy Chicken Burger",
        "description": "Pollo crispy, cheddar, lechuga, tomate y mayonesa de ajo en pan brioche.",
        "category": "Hamburguesas",
        "variants": [
            {
                "name": "Clásica",
                "price": "7900.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Pollo crispy", False),
                    ("Queso cheddar", True),
                    ("Lechuga", True),
                    ("Tomate", True),
                    ("Mayonesa de ajo", True),
                ],
            },
            {
                "name": "Spicy",
                "price": "8200.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Pollo crispy", False),
                    ("Queso cheddar", True),
                    ("Lechuga", True),
                    ("Tomate", True),
                    ("Mayonesa picante", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 4,
                "options": [
                    ("Cheddar extra", "900.00"),
                    ("Panceta crocante", "1300.00"),
                    ("Huevo a la plancha", "900.00"),
                    ("Pepinillos", "500.00"),
                ],
            },
            {
                "name": "Salsas extra",
                "min": 0,
                "max": 3,
                "options": [
                    ("Mayonesa de ajo", "350.00"),
                    ("Mayonesa picante", "450.00"),
                    ("Barbacoa", "450.00"),
                ],
            },
        ],
    },
    {
        "name": "Veggie Burger",
        "description": "Medallón veggie, queso, rúcula, tomate, cebolla morada y alioli en pan de papa.",
        "category": "Hamburguesas",
        "variants": [
            {
                "name": "Única",
                "price": "7600.00",
                "ingredients": [
                    ("Pan de papa", False),
                    ("Medallón veggie", False),
                    ("Queso tybo", True),
                    ("Rúcula", True),
                    ("Tomate", True),
                    ("Cebolla morada", True),
                    ("Alioli", True),
                ],
            }
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 4,
                "options": [
                    ("Queso extra", "900.00"),
                    ("Huevo a la plancha", "900.00"),
                    ("Cebolla caramelizada", "800.00"),
                    ("Palta", "1500.00"),
                ],
            },
            {
                "name": "Salsas extra",
                "min": 0,
                "max": 2,
                "options": [
                    ("Alioli extra", "450.00"),
                    ("Ketchup", "0.00"),
                    ("Mostaza", "0.00"),
                ],
            },
        ],
    },
    # -------------------------------------------------------------------------
    # COMBOS
    # -------------------------------------------------------------------------
    {
        "name": "Combo Burger",
        "description": "Classic Burger con guarnición y bebida. Elegí las opciones del combo.",
        "category": "Combos",
        "variants": [
            {
                "name": "Simple",
                "price": "11500.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Medallón de carne 120 g", False),
                    ("Queso cheddar", True),
                    ("Lechuga", True),
                    ("Tomate", True),
                    ("Cebolla morada", True),
                    ("Salsa de la casa", True),
                ],
            },
            {
                "name": "Doble",
                "price": "13100.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Medallón de carne 120 g", False),
                    ("Queso cheddar", True),
                    ("Lechuga", True),
                    ("Tomate", True),
                    ("Cebolla morada", True),
                    ("Salsa de la casa", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Elegí tu guarnición",
                "min": 0,
                "max": 1,
                "options": [
                    ("Papas clásicas", "0.00"),
                    ("Papas rústicas", "500.00"),
                    ("Aros de cebolla", "900.00"),
                    ("Papas cheddar", "1200.00"),
                ],
            },
            {
                "name": "Elegí tu bebida",
                "min": 1,
                "max": 1,
                "options": [
                    ("Coca-Cola 500 ml", "0.00"),
                    ("Coca-Cola Zero 500 ml", "0.00"),
                    ("Sprite 500 ml", "0.00"),
                    ("Agua sin gas 500 ml", "0.00"),
                ],
            },
            {
                "name": "Extras",
                "min": 0,
                "max": 4,
                "options": [
                    ("Cheddar extra", "900.00"),
                    ("Panceta crocante", "1300.00"),
                    ("Huevo a la plancha", "900.00"),
                    ("Medallón de carne extra", "2200.00"),
                ],
            },
        ],
    },
    {
        "name": "Combo Crispy",
        "description": "Crispy Chicken Burger con guarnición y bebida.",
        "category": "Combos",
        "variants": [
            {
                "name": "Clásico",
                "price": "11200.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Pollo crispy", False),
                    ("Queso cheddar", True),
                    ("Lechuga", True),
                    ("Tomate", True),
                    ("Mayonesa de ajo", True),
                ],
            },
            {
                "name": "Spicy",
                "price": "11500.00",
                "ingredients": [
                    ("Pan brioche", False),
                    ("Pollo crispy", False),
                    ("Queso cheddar", True),
                    ("Lechuga", True),
                    ("Tomate", True),
                    ("Mayonesa picante", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Elegí tu guarnición",
                "min": 0,
                "max": 1,
                "options": [
                    ("Papas clásicas", "0.00"),
                    ("Papas rústicas", "500.00"),
                    ("Aros de cebolla", "900.00"),
                ],
            },
            {
                "name": "Elegí tu bebida",
                "min": 1,
                "max": 1,
                "options": [
                    ("Coca-Cola 500 ml", "0.00"),
                    ("Coca-Cola Zero 500 ml", "0.00"),
                    ("Sprite 500 ml", "0.00"),
                    ("Agua sin gas 500 ml", "0.00"),
                ],
            },
            {
                "name": "Extras",
                "min": 0,
                "max": 3,
                "options": [
                    ("Cheddar extra", "900.00"),
                    ("Panceta crocante", "1300.00"),
                    ("Salsa picante extra", "450.00"),
                ],
            },
        ],
    },
    # -------------------------------------------------------------------------
    # PIZZAS
    # -------------------------------------------------------------------------
    {
        "name": "Pizza Muzzarella",
        "description": "Salsa de tomate, muzzarella, aceitunas verdes y orégano.",
        "category": "Pizzas",
        "variants": [
            {
                "name": "Individual",
                "price": "6900.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Salsa de tomate", True),
                    ("Muzzarella", True),
                    ("Aceitunas verdes", True),
                    ("Orégano", True),
                ],
            },
            {
                "name": "Grande",
                "price": "11200.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Salsa de tomate", True),
                    ("Muzzarella", True),
                    ("Aceitunas verdes", True),
                    ("Orégano", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Agregados",
                "min": 0,
                "max": 5,
                "options": [
                    ("Muzzarella extra", "1400.00"),
                    ("Jamón", "1200.00"),
                    ("Huevo", "900.00"),
                    ("Morrón", "900.00"),
                    ("Cebolla", "700.00"),
                    ("Aceitunas extra", "600.00"),
                ],
            }
        ],
    },
    {
        "name": "Pizza Napolitana",
        "description": "Muzzarella, tomate en rodajas, ajo, aceitunas verdes y orégano.",
        "category": "Pizzas",
        "variants": [
            {
                "name": "Individual",
                "price": "7600.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Salsa de tomate", True),
                    ("Muzzarella", True),
                    ("Tomate", True),
                    ("Ajo", True),
                    ("Aceitunas verdes", True),
                    ("Orégano", True),
                ],
            },
            {
                "name": "Grande",
                "price": "12400.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Salsa de tomate", True),
                    ("Muzzarella", True),
                    ("Tomate", True),
                    ("Ajo", True),
                    ("Aceitunas verdes", True),
                    ("Orégano", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Agregados",
                "min": 0,
                "max": 5,
                "options": [
                    ("Muzzarella extra", "1400.00"),
                    ("Jamón", "1200.00"),
                    ("Huevo", "900.00"),
                    ("Morrón", "900.00"),
                    ("Anchoas", "1600.00"),
                ],
            }
        ],
    },
    {
        "name": "Pizza Especial",
        "description": "Muzzarella, jamón cocido, morrón, aceitunas verdes y orégano.",
        "category": "Pizzas",
        "variants": [
            {
                "name": "Individual",
                "price": "8100.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Salsa de tomate", True),
                    ("Muzzarella", True),
                    ("Jamón cocido", True),
                    ("Morrón", True),
                    ("Aceitunas verdes", True),
                    ("Orégano", True),
                ],
            },
            {
                "name": "Grande",
                "price": "13200.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Salsa de tomate", True),
                    ("Muzzarella", True),
                    ("Jamón cocido", True),
                    ("Morrón", True),
                    ("Aceitunas verdes", True),
                    ("Orégano", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Agregados",
                "min": 0,
                "max": 5,
                "options": [
                    ("Muzzarella extra", "1400.00"),
                    ("Jamón extra", "1200.00"),
                    ("Huevo", "900.00"),
                    ("Morrón extra", "900.00"),
                    ("Aceitunas extra", "600.00"),
                ],
            }
        ],
    },
    {
        "name": "Pizza Fugazzeta",
        "description": "Muzzarella, cebolla, parmesano, aceitunas negras y orégano.",
        "category": "Pizzas",
        "variants": [
            {
                "name": "Individual",
                "price": "7800.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Muzzarella", True),
                    ("Cebolla", True),
                    ("Queso parmesano", True),
                    ("Aceitunas negras", True),
                    ("Orégano", True),
                ],
            },
            {
                "name": "Grande",
                "price": "12800.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Muzzarella", True),
                    ("Cebolla", True),
                    ("Queso parmesano", True),
                    ("Aceitunas negras", True),
                    ("Orégano", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Agregados",
                "min": 0,
                "max": 4,
                "options": [
                    ("Muzzarella extra", "1400.00"),
                    ("Jamón", "1200.00"),
                    ("Panceta", "1400.00"),
                    ("Huevo", "900.00"),
                ],
            }
        ],
    },
    {
        "name": "Pizza Pepperoni",
        "description": "Salsa de tomate, muzzarella, pepperoni, aceitunas negras y orégano.",
        "category": "Pizzas",
        "variants": [
            {
                "name": "Individual",
                "price": "8300.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Salsa de tomate", True),
                    ("Muzzarella", True),
                    ("Pepperoni", True),
                    ("Aceitunas negras", True),
                    ("Orégano", True),
                ],
            },
            {
                "name": "Grande",
                "price": "13600.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Salsa de tomate", True),
                    ("Muzzarella", True),
                    ("Pepperoni", True),
                    ("Aceitunas negras", True),
                    ("Orégano", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Agregados",
                "min": 0,
                "max": 4,
                "options": [
                    ("Muzzarella extra", "1400.00"),
                    ("Pepperoni extra", "1500.00"),
                    ("Jalapeños", "900.00"),
                    ("Cebolla", "700.00"),
                ],
            }
        ],
    },
    {
        "name": "Pizza Cuatro Quesos",
        "description": "Muzzarella, provolone, roquefort, parmesano, aceitunas negras y orégano.",
        "category": "Pizzas",
        "variants": [
            {
                "name": "Individual",
                "price": "8900.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Muzzarella", True),
                    ("Queso provolone", True),
                    ("Queso roquefort", True),
                    ("Queso parmesano", True),
                    ("Aceitunas negras", True),
                    ("Orégano", True),
                ],
            },
            {
                "name": "Grande",
                "price": "14500.00",
                "ingredients": [
                    ("Masa de pizza", False),
                    ("Muzzarella", True),
                    ("Queso provolone", True),
                    ("Queso roquefort", True),
                    ("Queso parmesano", True),
                    ("Aceitunas negras", True),
                    ("Orégano", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Agregados",
                "min": 0,
                "max": 4,
                "options": [
                    ("Muzzarella extra", "1400.00"),
                    ("Panceta", "1400.00"),
                    ("Cebolla caramelizada", "900.00"),
                    ("Nueces", "900.00"),
                ],
            }
        ],
    },
    # -------------------------------------------------------------------------
    # LOMITOS Y SÁNDWICHES
    # -------------------------------------------------------------------------
    {
        "name": "Lomito Completo",
        "description": "Lomo, jamón, queso, huevo, lechuga, tomate y mayonesa en pan tostado.",
        "category": "Lomitos y Sándwiches",
        "variants": [
            {
                "name": "Individual",
                "price": "9800.00",
                "ingredients": [
                    ("Pan de lomito", False),
                    ("Bife de lomo", False),
                    ("Jamón cocido", True),
                    ("Queso tybo", True),
                    ("Huevo", True),
                    ("Lechuga", True),
                    ("Tomate", True),
                    ("Mayonesa", True),
                ],
            }
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 5,
                "options": [
                    ("Lomo extra", "2500.00"),
                    ("Jamón extra", "900.00"),
                    ("Queso extra", "900.00"),
                    ("Huevo extra", "800.00"),
                    ("Panceta", "1300.00"),
                ],
            },
            {
                "name": "Salsas extra",
                "min": 0,
                "max": 3,
                "options": [
                    ("Mayonesa", "0.00"),
                    ("Ketchup", "0.00"),
                    ("Mostaza", "0.00"),
                    ("Alioli", "450.00"),
                ],
            },
        ],
    },
    {
        "name": "Lomito Cheddar Bacon",
        "description": "Lomo, cheddar, panceta, cebolla caramelizada y salsa especial en pan tostado.",
        "category": "Lomitos y Sándwiches",
        "variants": [
            {
                "name": "Individual",
                "price": "10800.00",
                "ingredients": [
                    ("Pan de lomito", False),
                    ("Bife de lomo", False),
                    ("Queso cheddar", True),
                    ("Panceta", True),
                    ("Cebolla caramelizada", True),
                    ("Salsa especial", True),
                ],
            }
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 4,
                "options": [
                    ("Lomo extra", "2500.00"),
                    ("Cheddar extra", "900.00"),
                    ("Panceta extra", "1300.00"),
                    ("Huevo", "800.00"),
                ],
            },
            {
                "name": "Salsas extra",
                "min": 0,
                "max": 2,
                "options": [
                    ("Salsa especial extra", "450.00"),
                    ("Barbacoa", "450.00"),
                    ("Alioli", "450.00"),
                ],
            },
        ],
    },
    {
        "name": "Sándwich de Milanesa Completo",
        "description": "Milanesa, jamón, queso, huevo, lechuga, tomate y mayonesa.",
        "category": "Lomitos y Sándwiches",
        "variants": [
            {
                "name": "Carne",
                "price": "9000.00",
                "ingredients": [
                    ("Pan de sándwich", False),
                    ("Milanesa de carne", False),
                    ("Jamón cocido", True),
                    ("Queso tybo", True),
                    ("Huevo", True),
                    ("Lechuga", True),
                    ("Tomate", True),
                    ("Mayonesa", True),
                ],
            },
            {
                "name": "Pollo",
                "price": "8800.00",
                "ingredients": [
                    ("Pan de sándwich", False),
                    ("Milanesa de pollo", False),
                    ("Jamón cocido", True),
                    ("Queso tybo", True),
                    ("Huevo", True),
                    ("Lechuga", True),
                    ("Tomate", True),
                    ("Mayonesa", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 4,
                "options": [
                    ("Jamón extra", "900.00"),
                    ("Queso extra", "900.00"),
                    ("Huevo extra", "800.00"),
                    ("Panceta", "1300.00"),
                ],
            },
            {
                "name": "Salsas extra",
                "min": 0,
                "max": 3,
                "options": [
                    ("Mayonesa", "0.00"),
                    ("Ketchup", "0.00"),
                    ("Mostaza", "0.00"),
                    ("Alioli", "450.00"),
                ],
            },
        ],
    },
    # -------------------------------------------------------------------------
    # MILANESAS AL PLATO
    # -------------------------------------------------------------------------
    {
        "name": "Milanesa Clásica",
        "description": "Milanesa al plato. Elegí carne o pollo y una guarnición.",
        "category": "Milanesas",
        "variants": [
            {
                "name": "Carne",
                "price": "8500.00",
                "ingredients": [("Milanesa de carne", False)],
            },
            {
                "name": "Pollo",
                "price": "8200.00",
                "ingredients": [("Milanesa de pollo", False)],
            },
        ],
        "modifier_groups": [
            {
                "name": "Elegí tu guarnición",
                "min": 0,
                "max": 1,
                "options": [
                    ("Papas fritas", "0.00"),
                    ("Puré de papas", "0.00"),
                    ("Ensalada mixta", "0.00"),
                    ("Papas rústicas", "500.00"),
                ],
            },
            {
                "name": "Extras",
                "min": 0,
                "max": 3,
                "options": [
                    ("Huevo frito", "900.00"),
                    ("Cheddar", "1100.00"),
                    ("Panceta", "1300.00"),
                ],
            },
        ],
    },
    {
        "name": "Milanesa Napolitana",
        "description": "Milanesa con salsa de tomate, jamón, muzzarella y orégano. Incluye una guarnición.",
        "category": "Milanesas",
        "variants": [
            {
                "name": "Carne",
                "price": "9900.00",
                "ingredients": [
                    ("Milanesa de carne", False),
                    ("Salsa de tomate", True),
                    ("Jamón cocido", True),
                    ("Muzzarella", True),
                    ("Orégano", True),
                ],
            },
            {
                "name": "Pollo",
                "price": "9600.00",
                "ingredients": [
                    ("Milanesa de pollo", False),
                    ("Salsa de tomate", True),
                    ("Jamón cocido", True),
                    ("Muzzarella", True),
                    ("Orégano", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Elegí tu guarnición",
                "min": 0,
                "max": 1,
                "options": [
                    ("Papas fritas", "0.00"),
                    ("Puré de papas", "0.00"),
                    ("Ensalada mixta", "0.00"),
                    ("Papas rústicas", "500.00"),
                ],
            },
            {
                "name": "Extras",
                "min": 0,
                "max": 3,
                "options": [
                    ("Muzzarella extra", "1100.00"),
                    ("Jamón extra", "900.00"),
                    ("Huevo frito", "900.00"),
                ],
            },
        ],
    },
    {
        "name": "Milanesa Cheddar & Bacon",
        "description": "Milanesa con salsa cheddar, panceta crocante y verdeo. Incluye una guarnición.",
        "category": "Milanesas",
        "variants": [
            {
                "name": "Carne",
                "price": "10400.00",
                "ingredients": [
                    ("Milanesa de carne", False),
                    ("Salsa cheddar", True),
                    ("Panceta", True),
                    ("Verdeo", True),
                ],
            },
            {
                "name": "Pollo",
                "price": "10100.00",
                "ingredients": [
                    ("Milanesa de pollo", False),
                    ("Salsa cheddar", True),
                    ("Panceta", True),
                    ("Verdeo", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Elegí tu guarnición",
                "min": 0,
                "max": 1,
                "options": [
                    ("Papas fritas", "0.00"),
                    ("Puré de papas", "0.00"),
                    ("Ensalada mixta", "0.00"),
                    ("Papas rústicas", "500.00"),
                ],
            },
            {
                "name": "Extras",
                "min": 0,
                "max": 3,
                "options": [
                    ("Cheddar extra", "1100.00"),
                    ("Panceta extra", "1300.00"),
                    ("Huevo frito", "900.00"),
                ],
            },
        ],
    },
    # -------------------------------------------------------------------------
    # PAPAS Y ACOMPAÑAMIENTOS
    # -------------------------------------------------------------------------
    {
        "name": "Papas Fritas",
        "description": "Papas fritas doradas y crocantes.",
        "category": "Papas y Acompañamientos",
        "variants": [
            {"name": "Individual", "price": "3500.00", "ingredients": [("Papas fritas", False), ("Sal", True)]},
            {"name": "Grande", "price": "5200.00", "ingredients": [("Papas fritas", False), ("Sal", True)]},
        ],
        "modifier_groups": [
            {
                "name": "Toppings",
                "min": 0,
                "max": 4,
                "options": [
                    ("Salsa cheddar", "1100.00"),
                    ("Panceta crocante", "1300.00"),
                    ("Verdeo", "500.00"),
                    ("Huevo frito", "900.00"),
                ],
            },
            {
                "name": "Dips",
                "min": 0,
                "max": 3,
                "options": [
                    ("Ketchup", "0.00"),
                    ("Mayonesa", "0.00"),
                    ("Alioli", "450.00"),
                    ("Barbacoa", "450.00"),
                ],
            },
        ],
    },
    {
        "name": "Papas Cheddar & Bacon",
        "description": "Papas fritas con salsa cheddar, panceta crocante y verdeo.",
        "category": "Papas y Acompañamientos",
        "variants": [
            {
                "name": "Individual",
                "price": "5200.00",
                "ingredients": [
                    ("Papas fritas", False),
                    ("Salsa cheddar", True),
                    ("Panceta", True),
                    ("Verdeo", True),
                ],
            },
            {
                "name": "Grande",
                "price": "7200.00",
                "ingredients": [
                    ("Papas fritas", False),
                    ("Salsa cheddar", True),
                    ("Panceta", True),
                    ("Verdeo", True),
                ],
            },
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 3,
                "options": [
                    ("Cheddar extra", "1100.00"),
                    ("Panceta extra", "1300.00"),
                    ("Huevo frito", "900.00"),
                ],
            }
        ],
    },
    {
        "name": "Papas Rústicas",
        "description": "Papas con piel, especias y alioli casero.",
        "category": "Papas y Acompañamientos",
        "variants": [
            {
                "name": "Individual",
                "price": "4100.00",
                "ingredients": [("Papas rústicas", False), ("Mix de especias", True), ("Alioli", True)],
            },
            {
                "name": "Grande",
                "price": "5900.00",
                "ingredients": [("Papas rústicas", False), ("Mix de especias", True), ("Alioli", True)],
            },
        ],
        "modifier_groups": [
            {
                "name": "Dips extra",
                "min": 0,
                "max": 3,
                "options": [
                    ("Alioli", "450.00"),
                    ("Barbacoa", "450.00"),
                    ("Cheddar", "600.00"),
                    ("Mayonesa picante", "450.00"),
                ],
            }
        ],
    },
    # -------------------------------------------------------------------------
    # ENTRADAS
    # -------------------------------------------------------------------------
    {
        "name": "Aros de Cebolla",
        "description": "Aros de cebolla rebozados y crocantes.",
        "category": "Entradas",
        "variants": [
            {"name": "8 unidades", "price": "4200.00", "ingredients": [("Aros de cebolla", False)]},
            {"name": "12 unidades", "price": "5600.00", "ingredients": [("Aros de cebolla", False)]},
        ],
        "modifier_groups": [
            {
                "name": "Elegí tu dip",
                "min": 0,
                "max": 1,
                "options": [
                    ("Ketchup", "0.00"),
                    ("Barbacoa", "0.00"),
                    ("Alioli", "0.00"),
                    ("Mayonesa picante", "0.00"),
                ],
            },
            {
                "name": "Dip extra",
                "min": 0,
                "max": 2,
                "options": [
                    ("Cheddar", "600.00"),
                    ("Alioli", "450.00"),
                    ("Barbacoa", "450.00"),
                ],
            },
        ],
    },
    {
        "name": "Chicken Fingers",
        "description": "Tiras de pollo crispy acompañadas con dip a elección.",
        "category": "Entradas",
        "variants": [
            {"name": "5 unidades", "price": "5200.00", "ingredients": [("Tiras de pollo crispy", False)]},
            {"name": "8 unidades", "price": "6900.00", "ingredients": [("Tiras de pollo crispy", False)]},
        ],
        "modifier_groups": [
            {
                "name": "Elegí tu dip",
                "min": 0,
                "max": 1,
                "options": [
                    ("Barbacoa", "0.00"),
                    ("Alioli", "0.00"),
                    ("Mayonesa picante", "0.00"),
                    ("Cheddar", "150.00"),
                ],
            },
            {
                "name": "Dip extra",
                "min": 0,
                "max": 2,
                "options": [
                    ("Cheddar", "600.00"),
                    ("Alioli", "450.00"),
                    ("Barbacoa", "450.00"),
                ],
            },
        ],
    },
    {
        "name": "Bastones de Muzzarella",
        "description": "Bastones de muzzarella rebozados con salsa de tomate especiada.",
        "category": "Entradas",
        "variants": [
            {"name": "6 unidades", "price": "5600.00", "ingredients": [("Bastones de muzzarella", False), ("Salsa de tomate especiada", True)]}
        ],
        "modifier_groups": [
            {
                "name": "Dips extra",
                "min": 0,
                "max": 2,
                "options": [
                    ("Salsa de tomate extra", "350.00"),
                    ("Alioli", "450.00"),
                    ("Barbacoa", "450.00"),
                ],
            }
        ],
    },
    # -------------------------------------------------------------------------
    # ENSALADAS
    # -------------------------------------------------------------------------
    {
        "name": "Ensalada Caesar",
        "description": "Lechuga, pollo grillado, croutons, parmesano y aderezo Caesar.",
        "category": "Ensaladas",
        "variants": [
            {
                "name": "Clásica",
                "price": "7200.00",
                "ingredients": [
                    ("Lechuga", True),
                    ("Pollo grillado", True),
                    ("Croutons", True),
                    ("Queso parmesano", True),
                    ("Aderezo Caesar", True),
                ],
            }
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 3,
                "options": [
                    ("Pollo extra", "1800.00"),
                    ("Parmesano extra", "700.00"),
                    ("Palta", "1500.00"),
                ],
            },
            {
                "name": "Aderezo extra",
                "min": 0,
                "max": 2,
                "options": [
                    ("Caesar", "350.00"),
                    ("Oliva y limón", "350.00"),
                ],
            },
        ],
    },
    {
        "name": "Ensalada Mediterránea",
        "description": "Mix de verdes, tomate, cebolla morada, aceitunas negras, queso y vinagreta.",
        "category": "Ensaladas",
        "variants": [
            {
                "name": "Clásica",
                "price": "6800.00",
                "ingredients": [
                    ("Mix de verdes", True),
                    ("Tomate", True),
                    ("Cebolla morada", True),
                    ("Aceitunas negras", True),
                    ("Queso en cubos", True),
                    ("Vinagreta", True),
                ],
            }
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 3,
                "options": [
                    ("Pollo grillado", "1800.00"),
                    ("Palta", "1500.00"),
                    ("Huevo", "800.00"),
                ],
            }
        ],
    },
    # -------------------------------------------------------------------------
    # BEBIDAS
    # -------------------------------------------------------------------------
    {
        "name": "Coca-Cola",
        "description": "Gaseosa Coca-Cola.",
        "category": "Bebidas",
        "variants": [
            {"name": "500 ml", "price": "2200.00", "ingredients": []},
            {"name": "1,5 L", "price": "4200.00", "ingredients": []},
        ],
        "modifier_groups": [],
    },
    {
        "name": "Coca-Cola Zero",
        "description": "Gaseosa Coca-Cola sin azúcar.",
        "category": "Bebidas",
        "variants": [
            {"name": "500 ml", "price": "2200.00", "ingredients": []},
            {"name": "1,5 L", "price": "4200.00", "ingredients": []},
        ],
        "modifier_groups": [],
    },
    {
        "name": "Sprite",
        "description": "Gaseosa lima-limón.",
        "category": "Bebidas",
        "variants": [
            {"name": "500 ml", "price": "2200.00", "ingredients": []},
            {"name": "1,5 L", "price": "4200.00", "ingredients": []},
        ],
        "modifier_groups": [],
    },
    {
        "name": "Agua Mineral",
        "description": "Agua mineral fresca.",
        "category": "Bebidas",
        "variants": [
            {"name": "Sin gas 500 ml", "price": "1700.00", "ingredients": []},
            {"name": "Con gas 500 ml", "price": "1800.00", "ingredients": []},
        ],
        "modifier_groups": [],
    },
    {
        "name": "Limonada Casera",
        "description": "Limonada natural con limón, menta y jengibre.",
        "category": "Bebidas",
        "variants": [
            {
                "name": "500 ml",
                "price": "3100.00",
                "ingredients": [("Limón", False), ("Menta", True), ("Jengibre", True), ("Azúcar", True)],
            },
            {
                "name": "1 L",
                "price": "5200.00",
                "ingredients": [("Limón", False), ("Menta", True), ("Jengibre", True), ("Azúcar", True)],
            },
        ],
        "modifier_groups": [
            {
                "name": "Endulzado",
                "min": 1,
                "max": 1,
                "options": [
                    ("Con azúcar", "0.00"),
                    ("Sin azúcar", "0.00"),
                    ("Con edulcorante", "0.00"),
                ],
            }
        ],
    },
    # -------------------------------------------------------------------------
    # POSTRES
    # -------------------------------------------------------------------------
    {
        "name": "Chocotorta",
        "description": "Porción de chocotorta clásica con dulce de leche y queso crema.",
        "category": "Postres",
        "variants": [
            {
                "name": "Porción",
                "price": "4200.00",
                "ingredients": [("Galletitas de chocolate", False), ("Dulce de leche", False), ("Queso crema", False)],
            }
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 2,
                "options": [
                    ("Dulce de leche extra", "700.00"),
                    ("Salsa de chocolate", "600.00"),
                ],
            }
        ],
    },
    {
        "name": "Brownie con Helado",
        "description": "Brownie tibio de chocolate con helado de crema americana y salsa de chocolate.",
        "category": "Postres",
        "variants": [
            {
                "name": "Porción",
                "price": "4900.00",
                "ingredients": [("Brownie de chocolate", False), ("Helado de crema americana", True), ("Salsa de chocolate", True)],
            }
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 3,
                "options": [
                    ("Bocha de helado extra", "1100.00"),
                    ("Dulce de leche", "700.00"),
                    ("Nueces", "700.00"),
                ],
            }
        ],
    },
    {
        "name": "Cheesecake de Frutos Rojos",
        "description": "Cheesecake cremoso con salsa de frutos rojos.",
        "category": "Postres",
        "variants": [
            {
                "name": "Porción",
                "price": "4600.00",
                "ingredients": [("Cheesecake", False), ("Salsa de frutos rojos", True)],
            }
        ],
        "modifier_groups": [
            {
                "name": "Extras",
                "min": 0,
                "max": 2,
                "options": [
                    ("Salsa de frutos rojos extra", "600.00"),
                    ("Dulce de leche", "700.00"),
                ],
            }
        ],
    },
    {
        "name": "Helado",
        "description": "Helado artesanal. Elegí tus sabores.",
        "category": "Postres",
        "variants": [
            {"name": "2 bochas", "price": "3300.00", "ingredients": []},
            {"name": "3 bochas", "price": "4100.00", "ingredients": []},
        ],
        "modifier_groups": [
            {
                "name": "Sabores",
                "min": 1,
                "max": 3,
                "options": [
                    ("Crema americana", "0.00"),
                    ("Chocolate", "0.00"),
                    ("Dulce de leche", "0.00"),
                    ("Frutilla", "0.00"),
                    ("Limón", "0.00"),
                ],
            },
            {
                "name": "Toppings",
                "min": 0,
                "max": 3,
                "options": [
                    ("Salsa de chocolate", "500.00"),
                    ("Dulce de leche", "600.00"),
                    ("Galletitas Oreo", "700.00"),
                    ("Nueces", "700.00"),
                ],
            },
        ],
    },
]


CATEGORY_NAMES = [
    "Hamburguesas",
    "Combos",
    "Pizzas",
    "Lomitos y Sándwiches",
    "Milanesas",
    "Papas y Acompañamientos",
    "Entradas",
    "Ensaladas",
    "Bebidas",
    "Postres",
]


def clean_catalog(prisma: Prisma) -> None:
    """
    Remove catalog data in FK-safe order.

    The catalog cannot be deleted while OrderLine references ProductVariant
    (onDelete: Restrict), so this development seed clears order data first.
    Clients/conversations/business configuration are intentionally preserved.
    """
    logger.info("Cleaning transactional dependencies and catalog data...")

    # OrderLine children first.
    prisma.orderlinemodifier.delete_many()
    prisma.orderlineremovedingredient.delete_many()

    # Other order children, then lines/orders.
    prisma.payment.delete_many()
    prisma.appliedcoupon.delete_many()
    prisma.orderline.delete_many()
    prisma.order.delete_many()

    # Catalog dependents.
    prisma.modifieroption.delete_many()
    prisma.modifiergroup.delete_many()
    prisma.productvariantingredient.delete_many()
    prisma.price.delete_many()
    prisma.discount.delete_many()
    prisma.productvariant.delete_many()
    prisma.product.delete_many()
    prisma.ingredient.delete_many()
    prisma.category.delete_many()


def validate_catalog_data() -> None:
    """Fail fast if any catalog variant or modifier is missing a valid price."""
    for product in PRODUCTS:
        variants = product.get("variants", [])
        if not variants:
            raise ValueError(f"Product without variants: {product['name']}")

        for variant in variants:
            if "price" not in variant:
                raise ValueError(
                    f"Missing price for {product['name']} / {variant.get('name', '<unnamed>')}"
                )

            price = money(variant["price"])
            if price < 0:
                raise ValueError(
                    f"Negative price for {product['name']} / {variant['name']}: {price}"
                )

        for group in product.get("modifier_groups", []):
            for option_name, price_delta in group.get("options", []):
                delta = money(price_delta)
                if delta < 0:
                    raise ValueError(
                        f"Negative modifier price for {product['name']} / "
                        f"{group['name']} / {option_name}: {delta}"
                    )


def collect_ingredient_names() -> list[str]:
    names: set[str] = set()
    for product in PRODUCTS:
        for variant in product["variants"]:
            for ingredient_name, _removable in variant.get("ingredients", []):
                names.add(ingredient_name)
    return sorted(names)


def create_categories(prisma: Prisma) -> dict[str, str]:
    logger.info("Creating categories...")
    category_ids: dict[str, str] = {}

    for category_name in CATEGORY_NAMES:
        category = prisma.category.create(data={"description": category_name})
        category_ids[category_name] = category.id

    return category_ids


def create_ingredients(prisma: Prisma) -> dict[str, str]:
    logger.info("Creating ingredients...")
    ingredient_ids: dict[str, str] = {}

    for ingredient_name in collect_ingredient_names():
        ingredient = prisma.ingredient.create(data={"name": ingredient_name})
        ingredient_ids[ingredient_name] = ingredient.id

    return ingredient_ids


def create_modifier_groups(prisma: Prisma, product_id: str, groups: list[dict[str, Any]]) -> tuple[int, int]:
    group_count = 0
    option_count = 0

    for group_data in groups:
        group = prisma.modifiergroup.create(
            data={
                "productId": product_id,
                "name": group_data["name"],
                "minSelections": group_data["min"],
                "maxSelections": group_data["max"],
            }
        )
        group_count += 1

        for option_name, price_delta in group_data["options"]:
            prisma.modifieroption.create(
                data={
                    "modifierGroupId": group.id,
                    "name": option_name,
                    "priceDelta": money(price_delta),
                    "available": True,
                }
            )
            option_count += 1

    return group_count, option_count


def create_products(
    prisma: Prisma,
    category_ids: dict[str, str],
    ingredient_ids: dict[str, str],
    now: datetime,
) -> dict[str, int]:
    logger.info("Creating products, variants, prices, ingredients and modifier groups...")

    stats = {
        "products": 0,
        "variants": 0,
        "prices": 0,
        "variant_ingredients": 0,
        "modifier_groups": 0,
        "modifier_options": 0,
    }

    for product_data in PRODUCTS:
        category_name = product_data["category"]
        if category_name not in category_ids:
            raise ValueError(f"Unknown category in seed: {category_name}")

        product = prisma.product.create(
            data={
                "name": product_data["name"],
                "description": product_data["description"],
                "imageUrl": product_data.get("image_url"),
                "available": product_data.get("available", True),
                "categoryId": category_ids[category_name],
            }
        )
        stats["products"] += 1

        for variant_data in product_data["variants"]:
            variant = prisma.productvariant.create(
                data={
                    "productId": product.id,
                    "name": variant_data["name"],
                    "available": variant_data.get("available", True),
                }
            )
            stats["variants"] += 1

            # Price is a separate entity in the Prisma schema. Every variant
            # created by this seed receives one current price row.
            variant_price = money(variant_data["price"])
            prisma.price.create(
                data={
                    "productVariantId": variant.id,
                    "sinceDate": now,
                    "price": variant_price,
                }
            )
            stats["prices"] += 1

            seen_ingredients: set[str] = set()
            for ingredient_name, removable in variant_data.get("ingredients", []):
                if ingredient_name in seen_ingredients:
                    raise ValueError(
                        f"Duplicated ingredient '{ingredient_name}' in "
                        f"{product_data['name']} / {variant_data['name']}"
                    )
                seen_ingredients.add(ingredient_name)

                ingredient_id = ingredient_ids.get(ingredient_name)
                if ingredient_id is None:
                    raise ValueError(f"Ingredient was not created: {ingredient_name}")

                prisma.productvariantingredient.create(
                    data={
                        "productVariantId": variant.id,
                        "ingredientId": ingredient_id,
                        "removable": removable,
                    }
                )
                stats["variant_ingredients"] += 1

        group_count, option_count = create_modifier_groups(
            prisma,
            product.id,
            product_data.get("modifier_groups", []),
        )
        stats["modifier_groups"] += group_count
        stats["modifier_options"] += option_count

    return stats


def create_example_discounts(prisma: Prisma) -> int:
    """Create a few useful promotions to exercise both Discount relations."""
    count = 0

    veggie = prisma.product.find_first(where={"name": "Veggie Burger"})
    if veggie:
        prisma.discount.create(
            data={
                "percentage": money("10.00"),
                "productId": veggie.id,
            }
        )
        count += 1

    coca = prisma.product.find_first(where={"name": "Coca-Cola"})
    if coca:
        large_variant = prisma.productvariant.find_first(
            where={"productId": coca.id, "name": "1,5 L"}
        )
        if large_variant:
            prisma.discount.create(
                data={
                    "percentage": money("5.00"),
                    "productVariantId": large_variant.id,
                }
            )
            count += 1

    return count


def main() -> None:
    prisma = Prisma()
    prisma.connect()
    logger.info("Connected to Prisma. Starting Rapidfood seed...")

    try:
        validate_catalog_data()
        clean_catalog(prisma)

        now = datetime.now(timezone.utc)
        category_ids = create_categories(prisma)
        ingredient_ids = create_ingredients(prisma)
        stats = create_products(prisma, category_ids, ingredient_ids, now)
        discount_count = create_example_discounts(prisma)

        logger.info("Seed completed successfully.")
        logger.info("Categories: %s", len(category_ids))
        logger.info("Ingredients: %s", len(ingredient_ids))
        logger.info("Products: %s", stats["products"])
        logger.info("Variants: %s", stats["variants"])
        logger.info("Prices: %s", stats["prices"])
        logger.info("Variant ingredients: %s", stats["variant_ingredients"])
        logger.info("Modifier groups: %s", stats["modifier_groups"])
        logger.info("Modifier options: %s", stats["modifier_options"])
        logger.info("Discounts: %s", discount_count)

    except Exception:
        logger.exception("Error during seed")
        raise
    finally:
        prisma.disconnect()


if __name__ == "__main__":
    main()
