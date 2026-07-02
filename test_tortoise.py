import asyncio
from app.core.config import TORTOISE_ORM_CONFIG
from tortoise import Tortoise

async def main():
    try:
        await Tortoise.init(config=TORTOISE_ORM_CONFIG)
        print("Tortoise initialized successfully!")
        await Tortoise.close_connections()
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
