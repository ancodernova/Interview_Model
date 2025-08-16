import asyncio
from prisma import Prisma

db = Prisma()

async def main():
    await db.connect()

    # Create user
    user = await db.user.create(
        data={
            "username": "aniket",
            "email": "aniket@example.com",
            "passwordHash": "hashed_pw",
        }
    )
    print("Created:", user)

    # Fetch all users
    users = await db.user.find_many()
    print("Users:", users)

    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
