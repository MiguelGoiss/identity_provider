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
    from app.database.models.user_companies import UserCompany
    
    users = await User.all()
    count = 0
    for user in users:
        # Check if user has job_title or employee_number to copy
        if user.job_title or user.employee_number:
            # Find primary company first
            company = await UserCompany.filter(user=user, is_primary=True).first()
            if not company:
                # Fallback to the first company they are associated with
                company = await UserCompany.filter(user=user).first()
                
            if company:
                company.job_title = user.job_title
                company.employee_number = user.employee_number
                await company.save()
                count += 1
                
    print(f"Migration completed. Migrated company data for {count} users.")
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(run_migration())
