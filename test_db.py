import asyncio
from prisma import Prisma

async def main():
    db = Prisma()
    await db.connect()
    addresses = await db.address.find_many()
    for a in addresses:
        print(f"ID: {a.id}, Street: {a.street}, Number: {a.streetNumber}")
    await db.disconnect()

asyncio.run(main())
