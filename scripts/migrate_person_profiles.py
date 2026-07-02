import asyncio
from tortoise import Tortoise
from app.core.config import settings

async def init_db():
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={'models': ['app.database.models']}
    )

async def run_migration():
    await init_db()
    from app.database.models.user import User
    from app.database.models.person_profile import PersonProfile
    
    users = await User.all()
    count = 0
    for user in users:
        # Check if profile already exists just in case
        profile = await PersonProfile.get_or_none(user=user)
        if not profile:
            await PersonProfile.create(
                user=user,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name
            )
            count += 1
            
    print(f"Migration completed. Migrated {count} users.")
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(run_migration())
