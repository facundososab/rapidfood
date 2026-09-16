import logging
from decimal import Decimal
from datetime import datetime, timezone
from prisma import Prisma

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main() -> None:
    prisma = Prisma()
    prisma.connect()
    
    logger.info("Connected to Prisma. Starting seed...")

    try:
        # Delete existing data to ensure a clean state
        logger.info("Cleaning up existing data...")
        prisma.price.delete_many()
        prisma.product.delete_many()
        prisma.category.delete_many()

        # 1. Create Categories
        logger.info("Creating categories...")
        categories_data = [
            {"name": "Hamburguesas", "description": "Nuestras clásicas hamburguesas"},
            {"name": "Bebidas", "description": "Bebidas frías y refrescantes"},
            {"name": "Acompañamientos", "description": "Papas fritas, aros de cebolla y más"},
            {"name": "Postres", "description": "Algo dulce para terminar"},
            {"name": "Adicionales", "description": "Dips y salsas extra"}
        ]
        
        created_categories = {}
        for cat in categories_data:
            category = prisma.category.create(
                data={"description": cat["name"]}
            )
            created_categories[cat["name"]] = category.id

        now = datetime.now(timezone.utc)

        # 2. Create Products and Prices
        logger.info("Creating products and prices...")
        
        products_data = [
            # Hamburguesas
            {
                "name": "Hamburguesa Simple",
                "description": "Medallón de carne 120g, queso cheddar, lechuga y tomate.",
                "price": "5500.00",
                "category": "Hamburguesas",
                "available": True
            },
            {
                "name": "Hamburguesa Doble Cheese",
                "description": "Doble medallón de carne 120g y cuádruple queso cheddar.",
                "price": "7500.00",
                "category": "Hamburguesas",
                "available": True
            },
            {
                "name": "Bacon Burger",
                "description": "Medallón de carne 120g, queso cheddar, panceta crocante y salsa BBQ.",
                "price": "6800.00",
                "category": "Hamburguesas",
                "available": True
            },
            {
                "name": "Crispy Chicken Burger",
                "description": "Suprema de pollo crispy, lechuga repollada, tomate y mayonesa.",
                "price": "6000.00",
                "category": "Hamburguesas",
                "available": True
            },
            {
                "name": "Veggie Burger",
                "description": "Medallón de lentejas, lechuga, tomate, cebolla morada y veganesa.",
                "price": "5200.00",
                "category": "Hamburguesas",
                "available": True
            },
            
            # Bebidas
            {
                "name": "Coca Cola 500ml",
                "description": "Gaseosa sabor original 500ml.",
                "price": "1500.00",
                "category": "Bebidas",
                "available": True
            },
            {
                "name": "Coca Cola Zero 500ml",
                "description": "Gaseosa sin azúcar 500ml.",
                "price": "1500.00",
                "category": "Bebidas",
                "available": True
            },
            {
                "name": "Sprite 500ml",
                "description": "Gaseosa lima limón 500ml.",
                "price": "1500.00",
                "category": "Bebidas",
                "available": True
            },
            {
                "name": "Agua Mineral 500ml",
                "description": "Agua mineral sin gas.",
                "price": "1200.00",
                "category": "Bebidas",
                "available": True
            },
            {
                "name": "Cerveza Artesanal IPA",
                "description": "Pinta de cerveza IPA tirada.",
                "price": "3000.00",
                "category": "Bebidas",
                "available": True
            },
            
            # Acompañamientos
            {
                "name": "Papas Fritas Clásicas",
                "description": "Porción de papas fritas bastón.",
                "price": "2500.00",
                "category": "Acompañamientos",
                "available": True
            },
            {
                "name": "Papas Cheddar y Bacon",
                "description": "Papas fritas con salsa cheddar y panceta crocante.",
                "price": "3800.00",
                "category": "Acompañamientos",
                "available": True
            },
            {
                "name": "Aros de Cebolla",
                "description": "Porción de 8 aros de cebolla rebozados.",
                "price": "2800.00",
                "category": "Acompañamientos",
                "available": True
            },
            {
                "name": "Nuggets de Pollo",
                "description": "Porción de 10 nuggets de pollo crispy.",
                "price": "3500.00",
                "category": "Acompañamientos",
                "available": True
            },
            
            # Postres
            {
                "name": "Helado Americana con Oreos",
                "description": "Copa de helado de crema americana con trozos de galletitas Oreo.",
                "price": "2200.00",
                "category": "Postres",
                "available": True
            },
            {
                "name": "Chocotorta",
                "description": "Porción individual de chocotorta clásica.",
                "price": "2800.00",
                "category": "Postres",
                "available": True
            },
            
            # Adicionales
            {
                "name": "Dip de Cheddar",
                "description": "Salsa cheddar extra.",
                "price": "500.00",
                "category": "Adicionales",
                "available": True
            },
            {
                "name": "Dip de BBQ",
                "description": "Salsa barbacoa extra.",
                "price": "500.00",
                "category": "Adicionales",
                "available": True
            }
        ]

        for p_data in products_data:
            product = prisma.product.create(
                data={
                    "name": p_data["name"],
                    "description": p_data["description"],
                    "available": p_data["available"],
                    "category": {
                        "connect": {
                            "id": created_categories[p_data["category"]]
                        }
                    }
                }
            )
            
            prisma.price.create(
                data={
                    "price": Decimal(p_data["price"]),
                    "sinceDate": now,
                    "product": {
                        "connect": {
                            "id": product.id
                        }
                    }
                }
            )
            
        logger.info("Seed completed successfully!")

    except Exception as e:
        logger.error(f"Error during seed: {e}")
        raise
    finally:
        prisma.disconnect()

if __name__ == '__main__':
    main()
