import asyncio
from sqlalchemy import text
from app.db.database import AsyncSessionLocal

async def f():
    async with AsyncSessionLocal() as s:
        await s.execute(text("UPDATE candidates SET status='PENDING' WHERE status='pending'"))
        await s.execute(text("UPDATE candidates SET status='PROCESSING' WHERE status='processing'"))
        await s.execute(text("UPDATE candidates SET status='COMPLETED' WHERE status='completed'"))
        await s.execute(text("UPDATE candidates SET status='FAILED' WHERE status='failed'"))
        await s.commit()
        print('done')

asyncio.run(f())
