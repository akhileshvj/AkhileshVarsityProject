import asyncio

from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.persona import PersonaProfile
from app.models.user import User
from app.services.embedding_service import embedding_service


MOCK_PERSONAS = [
    {
        "email": "sarah.architect@example.com",
        "lifestyle": "Early riser, loves marathon running, sustainable living and minimalism.",
        "values": {"ambition": "high", "fitness": "daily", "environmentalism": "high"},
        "dealbreakers": {"smoking": False, "relocation": "open"},
    },
    {
        "email": "david.musician@example.com",
        "lifestyle": "Night owl, jazz guitarist, values travel, spontaneous weekend getaways.",
        "values": {"creativity": "high", "freedom": "essential", "career": "freelance"},
        "dealbreakers": {"smoking": True, "kids": "undecided"},
    },
    {
        "email": "priya.biotech@example.com",
        "lifestyle": "Lab researcher, enjoys cooking, hiking trails, and home book reading.",
        "values": {"family": "close", "growth": "continuous", "communication": "direct"},
        "dealbreakers": {"smoking": False, "relocation": "never"},
    },
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        for persona in MOCK_PERSONAS:
            user = User(
                email=persona["email"],
                hashed_password=get_password_hash("SeededPass123!"),
            )
            session.add(user)
            await session.flush()

            payload = embedding_service.build_embedding_payload(
                lifestyle_summary=persona["lifestyle"],
                core_values=persona["values"],
                dealbreakers=persona["dealbreakers"],
            )
            embedding = await embedding_service.generate_embedding(payload)

            session.add(
                PersonaProfile(
                    user_id=user.id,
                    lifestyle_summary=persona["lifestyle"],
                    core_values=persona["values"],
                    dealbreakers=persona["dealbreakers"],
                    embedding=embedding,
                )
            )

        await session.commit()
        print("Candidate profiles seeded with vector embeddings.")


if __name__ == "__main__":
    asyncio.run(seed())
