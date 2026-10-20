import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.persona import PersonaProfile
from app.services.embedding_service import embedding_service

MOCK_PERSONAS = [
    {
        "email": "sarah.architect@example.com",
        "lifestyle": "Early riser, marathon runner, minimalist, values deep conversations.",
        "values": {"ambition": "high", "fitness": "daily", "environmentalism": "high"},
        "dealbreakers": {"smoking": False, "relocation": "open"}
    },
    {
        "email": "david.musician@example.com",
        "lifestyle": "Night owl jazz performer who loves spontaneous weekend road trips.",
        "values": {"creativity": "essential", "freedom": "high"},
        "dealbreakers": {"smoking": True, "kids": "undecided"}
    },
    {
        "email": "priya.biotech@example.com",
        "lifestyle": "Research scientist who loves cooking, hiking, and quiet weekend reading.",
        "values": {"family": "close", "growth": "continuous"},
        "dealbreakers": {"smoking": False, "relocation": "never"}
    }
]

async def seed():
    async with AsyncSessionLocal() as session:
        for p in MOCK_PERSONAS:
            # Check if user already exists
            existing_user_query = await session.execute(
                select(User).where(User.email == p["email"])
            )
            existing_user = existing_user_query.scalar_one_or_none()

            if existing_user:
                print(f"Skipping {p['email']}: already exists.")
                continue

            user = User(email=p["email"], hashed_password=get_password_hash("SeededPass123!"))
            session.add(user)
            await session.flush()

            payload = embedding_service.build_embedding_payload(p["lifestyle"], p["values"], p["dealbreakers"])
            embedding = await embedding_service.generate_embedding(payload)

            persona = PersonaProfile(
                user_id=user.id,
                lifestyle_summary=p["lifestyle"],
                core_values=p["values"],
                dealbreakers=p["dealbreakers"],
                embedding=embedding
            )
            session.add(persona)
            print(f"Seeded {p['email']}.")

        await session.commit()
        print("Candidate profiles successfully seeded with embeddings.")

if __name__ == "__main__":
    asyncio.run(seed())