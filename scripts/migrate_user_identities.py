import asyncio
from tortoise import Tortoise
from app.core.config import TORTOISE_ORM_CONFIG
from app.database.models.user import User
from app.database.models.user_email import UserEmail
from app.database.models.user_identity import UserIdentity

async def migrate_user_identities():
    print("Connecting to database...")
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)

    print("Migrating usernames...")
    users = await User.exclude(username__isnull=True).exclude(username="").all()
    username_count = 0
    for user in users:
        # Check if already exists to make script idempotent
        exists = await UserIdentity.filter(identity_type="username", identifier=user.username).exists()
        if not exists:
            await UserIdentity.create(
                user=user,
                identity_type="username",
                identifier=user.username,
                is_primary=True,
                is_verified=True
            )
            username_count += 1
    
    print(f"Migrated {username_count} usernames.")

    print("Migrating primary emails...")
    emails = await UserEmail.filter(is_primary=True).prefetch_related("user").all()
    email_count = 0
    for email_obj in emails:
        exists = await UserIdentity.filter(identity_type="email", identifier=email_obj.email).exists()
        if not exists:
            await UserIdentity.create(
                user=email_obj.user,
                identity_type="email",
                identifier=email_obj.email,
                is_primary=True,
                is_verified=True
            )
            email_count += 1

    print(f"Migrated {email_count} primary emails.")
    
    await Tortoise.close_connections()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(migrate_user_identities())
