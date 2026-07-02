import asyncio
import os
import sys
import pandas as pd
from datetime import datetime

# Garante que o módulo 'app' é encontrado independentemente de onde o script é corrido
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tortoise import Tortoise
from app.core.config import TORTOISE_ORM_CONFIG
from app.database.models import User, Company, UserCompany, PersonProfile, PersonEmail, PersonContact, ContactType, UserIdentity
from app.crypto.globals import crypto_service, blind_indexer
from app.crypto.normalizers import normalize_text

async def main():
    print("🔌 A ligar à base de dados...")
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    
    file_path = "/workspace/output.xlsx"
    print(f"Lendo ficheiro: {file_path}")
    df = pd.read_excel(file_path)
    
    # Preencher NaN com strings vazias para evitar problemas
    df = df.fillna("")
    
    # Criar o ContactType TELEMOVEL se não existir
    contact_type, _ = await ContactType.get_or_create(
        slug="TELEMOVEL",
        defaults={"label": "Telemóvel"}
    )
    
    count = 0
    
    for idx, row in df.iterrows():
        empresa = str(row.get("empresa", "")).strip()
        email = str(row.get("email", "")).strip()
        nome = str(row.get("nome", "")).strip()
        nif = str(row.get("nif", "")).strip()
        codigo = str(row.get("codigo", "")).strip()
        telemovel = str(row.get("telemovel", "")).strip()
        data_nascimento = row.get("data_nascimento")
        
        if not nome and not email:
            continue
            
        if email:
            email_idx_check = blind_indexer.compute("person_email.email", normalize_text(email))
            if await PersonEmail.get_or_none(email_idx=email_idx_check):
                print(f"Skipping existing user by email: {email}")
                continue
                
        if nif:
            if nif.endswith('.0'): nif = nif[:-2]
            tax_idx_check = blind_indexer.compute("person_profile.tax_id", normalize_text(nif))
            if await PersonProfile.get_or_none(tax_id_idx=tax_idx_check):
                print(f"Skipping existing user by NIF: {nif}")
                continue
        
        # 1. Empresa
        if not empresa:
            empresa = "Empresa Base"
        company = await Company.get_or_none(name=empresa)
        if not company:
            base_acronym = empresa[:3].upper()
            acronym = base_acronym
            counter = 1
            while await Company.get_or_none(acronym=acronym):
                acronym = f"{base_acronym[:2]}{counter}"
                counter += 1
            company = await Company.create(name=empresa, acronym=acronym)
        
        # 2. User
        user = await User.create()
        
        # 3. UserCompany
        codigo_enc = None
        codigo_idx = None
        if codigo:
            if codigo.endswith('.0'): codigo = codigo[:-2]
            codigo_enc = crypto_service.encrypt(codigo, "user_company.employee_number")
            codigo_idx = blind_indexer.compute("user_company.employee_number", normalize_text(codigo))
            
        await UserCompany.create(
            user=user,
            company=company,
            is_primary=True,
            employee_number_enc=codigo_enc,
            employee_number_idx=codigo_idx
        )
        
        # 4. Email
        if email:
            email_enc = crypto_service.encrypt(email, "person_email.email")
            email_idx = blind_indexer.compute("person_email.email", normalize_text(email))
            await PersonEmail.create(
                user=user,
                is_primary=True,
                scope="personal",
                email_enc=email_enc,
                email_idx=email_idx
            )
            
        # 5. PersonProfile
        parts = nome.split()
        first_name = parts[0] if len(parts) > 0 else "Sem Nome"
        last_name = parts[-1] if len(parts) > 1 else ""
            
        nif_enc = None
        nif_idx = None
        if nif:
            if nif.endswith('.0'): nif = nif[:-2]
            nif_enc = crypto_service.encrypt(nif, "person_profile.tax_id")
            nif_idx = blind_indexer.compute("person_profile.tax_id", normalize_text(nif))
            
            # Identidade para auth
            ident_enc = crypto_service.encrypt(nif, "user_identity.identifier")
            ident_idx = blind_indexer.compute("user_identity.identifier", normalize_text(nif))
            await UserIdentity.create(
                user=user,
                identity_type="nif",
                identifier_enc=ident_enc,
                identifier_idx=ident_idx,
                is_primary=True
            )
            
        bdate_enc = None
        if data_nascimento and str(data_nascimento).strip():
            try:
                if isinstance(data_nascimento, pd.Timestamp) or isinstance(data_nascimento, datetime):
                    date_str = data_nascimento.strftime("%Y-%m-%d")
                else:
                    date_str = str(data_nascimento)[:10]
                bdate_enc = crypto_service.encrypt(date_str, "person_profile.birth_date")
            except Exception as e:
                print(f"Erro ao parsear data_nascimento: {data_nascimento}")
                bdate_enc = None
            
        full_name_enc = crypto_service.encrypt(nome, "person_profile.full_name") if nome else None
        full_name_idx = blind_indexer.compute("person_profile.full_name", normalize_text(nome)) if nome else None

        await PersonProfile.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            full_name_enc=full_name_enc,
            full_name_idx=full_name_idx,
            tax_id_enc=nif_enc,
            tax_id_idx=nif_idx,
            birth_date_enc=bdate_enc
        )
        
        # 6. PersonContact (Telemóvel)
        if telemovel:
            if telemovel.endswith('.0'): telemovel = telemovel[:-2]
            tel_enc = crypto_service.encrypt(telemovel, "person_contact.value")
            tel_idx = blind_indexer.compute("person_contact.value", normalize_text(telemovel))
            await PersonContact.create(
                user=user,
                contact_type=contact_type,
                scope="personal",
                value_enc=tel_enc,
                value_idx=tel_idx
            )
            
        count += 1
            
    print(f"✅ Feito! Foram inseridos {count} utilizadores.")
    await Tortoise.close_connections()

if __name__ == "__main__":
    asyncio.run(main())
