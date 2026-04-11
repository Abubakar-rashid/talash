import asyncio
from sqlalchemy import text
from app.db.database import AsyncSessionLocal

async def fix_enum():
    async with AsyncSessionLocal() as session:
        try:
            # We are trying to push "PENDING" to the enum but the DB likely has "pending".
            # This makes sure both variants are handled.
            await session.execute(text("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'PENDING'"))
            await session.execute(text("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'PROCESSING'"))
            await session.execute(text("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'COMPLETED'"))
            await session.execute(text("ALTER TYPE processing_status ADD VALUE IF NOT EXISTS 'FAILED'"))
            await session.commit()
            print("Successfully updated the Enum type in PostgreSQL.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fix_enum())
