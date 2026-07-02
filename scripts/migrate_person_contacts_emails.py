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
    from app.database.models.person_email import PersonEmail
    from app.database.models.person_contact import PersonContact
    
    users = await User.all()
    
    for user in users:
        # Resolve emails
        emails = await PersonEmail.filter(user=user, scope='company').all()
        has_primary = False
        for email in emails:
            if email.is_primary:
                if has_primary:
                    email.is_primary = False
                    await email.save()
                else:
                    has_primary = True
        if emails and not has_primary:
            emails[0].is_primary = True
            await emails[0].save()
            
        # Resolve contacts
        contacts = await PersonContact.filter(user=user, scope='company').all()
        has_primary_contact = False
        for contact in contacts:
            if contact.is_primary:
                if has_primary_contact:
                    contact.is_primary = False
                    await contact.save()
                else:
                    has_primary_contact = True
        if contacts and not has_primary_contact:
            contacts[0].is_primary = True
            await contacts[0].save()

    print("Migration of primary flags completed.")
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(run_migration())
