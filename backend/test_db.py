import asyncio
from app.db import engine

async def test_connection():
    try:
        async with engine.connect() as conn:
            print("✅ Successfully connected to the database!")
    except Exception as e:
        print(f"❌ Failed to connect to the database. Error:\n{e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())
