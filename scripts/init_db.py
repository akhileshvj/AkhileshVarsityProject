import asyncio

from sqlalchemy import text

from app.core.database import Base, engine
from app.models.negotiation import Negotiation
from app.models.persona import PersonaProfile
from app.models.user import User

del Negotiation, PersonaProfile, User


async def init_db() -> None:
    async with engine.begin() as conn:
        print("Enabling extensions (uuid-ossp, vector)...")
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables initialized successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
