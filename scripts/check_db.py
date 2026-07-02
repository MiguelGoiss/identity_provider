import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from tortoise import Tortoise
from app.core.config import TORTOISE_ORM_CONFIG
from app.database.models import PersonProfile, UserIdentity

async def main():
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    
    profiles = await PersonProfile.all().limit(3).values('id', 'tax_id', 'tax_id_key_version', 'tax_id_enc')
    identities = await UserIdentity.all().limit(3).values('id', 'identifier', 'identifier_key_version', 'identifier_enc')
    
    print("PersonProfiles:", profiles)
    print("UserIdentities:", identities)
    
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(main())
