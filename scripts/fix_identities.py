import asyncio
import os
import sys

# Garante que o módulo 'app' é encontrado independentemente de onde o script é corrido
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tortoise import Tortoise
from app.core.config import TORTOISE_ORM_CONFIG
from app.database.models import UserIdentity, PersonProfile
from app.crypto.globals import crypto_service, blind_indexer
from app.crypto.normalizers import normalize_text

async def main():
    print("🔌 A ligar à base de dados...")
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    
    # Obter todas as identidades do tipo 'email'
    identities = await UserIdentity.filter(identity_type="email").prefetch_related('user', 'user__profile')
    
    count = 0
    skipped_no_nif = 0
    
    for identity in identities:
        user = identity.user
        
        # Obter o profile do user para extrair o NIF
        profile = await PersonProfile.get_or_none(user=user)
        if not profile:
            continue
            
        nif = profile.tax_id # desencripta automaticamente
        
        if not nif:
            skipped_no_nif += 1
            continue
            
        # Converter a identidade para tipo 'nif' com o valor do nif
        nif_enc = crypto_service.encrypt(nif, "user_identity.identifier")
        nif_idx = blind_indexer.compute("user_identity.identifier", normalize_text(nif))
        
        # Verificar se já existe uma identidade com este nif_idx
        # Para evitar erros de unique constraint se executarmos o script várias vezes
        existing = await UserIdentity.filter(identifier_idx=nif_idx).first()
        if existing and existing.id != identity.id:
            # Já existe outro registo com este nif como identifier, apagamos o de email
            await identity.delete()
            count += 1
            continue
            
        identity.identity_type = "nif"
        identity.identifier_enc = nif_enc
        identity.identifier_idx = nif_idx
        
        await identity.save()
        count += 1
        
    print(f"✅ Feito! Foram convertidas/apagadas {count} identidades para NIF. Ignorados {skipped_no_nif} users sem NIF.")
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(main())
