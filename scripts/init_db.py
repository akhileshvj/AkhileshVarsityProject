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
        try:
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "vector";'))
        except Exception:
            print("Skipping PostgreSQL extension setup because the database is not a Postgres instance.")

        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)

        try:
            print("Configuring HNSW vector index on persona_profiles...")
            await conn.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS idx_persona_embedding_hnsw
                    ON persona_profiles
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = 16, ef_construction = 64);
                    """
                )
            )
        except Exception:
            print("Skipping HNSW index creation for the current database backend.")

        print("Database schema and indexes configured successfully.")


if __name__ == "__main__":
    asyncio.run(init_db())
