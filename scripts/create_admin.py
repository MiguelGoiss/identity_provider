"""
Script para criar um utilizador administrador inicial na base de dados.

Uso (dentro do container):
    python scripts/create_admin.py

Ou com variáveis personalizadas:
    ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=secret python scripts/create_admin.py
"""
import asyncio
import os
import sys

# Garante que o módulo 'app' é encontrado independentemente de onde o script é corrido
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tortoise import Tortoise
from app.core.config import TORTOISE_ORM_CONFIG
from app.core.security import get_password_hash
from app.database.models import User, PersonProfile, UserIdentity, Company, UserCompany, Role, Permission
from app.crypto.globals import crypto_service, blind_indexer
from app.crypto.normalizers import normalize_text


# ---------------------------------------------------------------------------
# Configuração do admin — pode ser sobreescrita por variáveis de ambiente
# ---------------------------------------------------------------------------
ADMIN_FIRST_NAME = os.getenv("ADMIN_FIRST_NAME", "Admin")
ADMIN_LAST_NAME  = os.getenv("ADMIN_LAST_NAME",  "Sistema")
ADMIN_EMAIL      = os.getenv("ADMIN_EMAIL",      "admin@sistema.local")
ADMIN_USERNAME   = os.getenv("ADMIN_USERNAME",   "admin")
ADMIN_PASSWORD   = os.getenv("ADMIN_PASSWORD",   "changeme123!")

# Empresa base — criada automaticamente se não existir
COMPANY_NAME    = os.getenv("COMPANY_NAME",    "Empresa Principal")
COMPANY_ACRONYM = os.getenv("COMPANY_ACRONYM", "EP")
# ---------------------------------------------------------------------------


async def main() -> None:
    print("🔌 A ligar à base de dados...")
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)

    # 1. Verificar se o username ou email já existe
    norm_u = normalize_text(ADMIN_USERNAME)
    norm_e = normalize_text(ADMIN_EMAIL)
    u_idx = blind_indexer.compute("user_identity.identifier", norm_u)
    e_idx = blind_indexer.compute("user_identity.identifier", norm_e)

    existing_identity = await UserIdentity.filter(
        identifier_idx__in=[u_idx, e_idx]
    ).prefetch_related("user").first()
    
    if existing_identity:
        print(f"⚠️  Já existe um utilizador com esse identifier. Apenas atualizando roles e permissões.")
        user = existing_identity.user
    else:
        # 2. Garantir que existe pelo menos uma empresa
        company = await Company.get_or_none(acronym=COMPANY_ACRONYM)
        if not company:
            company = await Company.create(
                name=COMPANY_NAME,
                acronym=COMPANY_ACRONYM,
            )
            print(f"🏢 Empresa criada: {company.name} ({company.acronym})")
        else:
            print(f"🏢 Empresa existente utilizada: {company.name} ({company.acronym})")

        # 3. Criar o utilizador
        hashed_pw = get_password_hash(ADMIN_PASSWORD)
        user = await User.create(hashed_password=hashed_pw)
        print(f"👤 Utilizador criado (id={user.id}, uuid={user.uuid})")

        # Associar utilizador à empresa (obrigatório pelas relações na BD)
        await UserCompany.create(
            user=user,
            company=company,
            is_primary=True,
        )
        print(f"🔗 Associado à empresa principal: {company.name}")

        # 4. Perfil
        full_name = f"{ADMIN_FIRST_NAME} {ADMIN_LAST_NAME}".strip()
        fn_enc = crypto_service.encrypt(full_name, "person_profile.full_name")
        fn_idx = blind_indexer.compute("person_profile.full_name", full_name)
        
        await PersonProfile.create(
            user=user,
            first_name=ADMIN_FIRST_NAME,
            last_name=ADMIN_LAST_NAME,
            full_name_enc=fn_enc,
            full_name_idx=fn_idx,
            full_name_key_version=1
        )
        print(f"📋 Perfil criado: {full_name}")

        # 5. Identidades (username + email)
        u_enc = crypto_service.encrypt(norm_u, "user_identity.identifier")
        await UserIdentity.create(
            user=user,
            identity_type="username",
            identifier_enc=u_enc,
            identifier_idx=u_idx,
            is_primary=True,
            is_verified=True,
        )
        
        e_enc = crypto_service.encrypt(norm_e, "user_identity.identifier")
        await UserIdentity.create(
            user=user,
            identity_type="email",
            identifier_enc=e_enc,
            identifier_idx=e_idx,
            is_primary=True,
            is_verified=True,
        )
        print(f"🔑 Identidades criadas: username='{ADMIN_USERNAME}', email='{ADMIN_EMAIL}'")

    # 6. Criar Role de Administrador e dar todas as permissões
    permission_slugs = [
        "user:read", "user:create", "user:edit", "user:delete",
        "user_company:create", "user_company:edit", "user_company:delete",
        "role:read", "role:create", "role:edit", "role:delete",
        "permission:manage", "permission:manage_advanced",
        "company:read", "company:create", "company:edit", "company:delete",
        "local:read", "local:create", "local:edit", "local:delete",
        "org_unit:read", "org_unit:create", "org_unit:edit", "org_unit:delete",
        "org_unit_type:read", "org_unit_type:create", "org_unit_type:edit", "org_unit_type:delete",
        "app_window:read", "app_window:create", "app_window:edit", "app_window:delete",
        "application:read", "application:create", "application:edit", "application:delete",
        "api_key:manage"
    ]
    
    permissions = []
    for slug in permission_slugs:
        perm, _ = await Permission.get_or_create(
            slug=slug,
            defaults={"description": f"Permissão total para {slug}"}
        )
        permissions.append(perm)

    admin_role, _ = await Role.get_or_create(
        name="Administrador de Sistema",
        company=None # Global role
    )
    await admin_role.permissions.add(*permissions)
    await admin_role.users.add(user)
    
    print(f"🛡️  Atribuído o role '{admin_role.name}' com {len(permissions)} permissões")

    await Tortoise.close_connections()

    print()
    print("✅ Utilizador administrador criado com sucesso!")
    print(f"   Username : {ADMIN_USERNAME}")
    print(f"   Email    : {ADMIN_EMAIL}")
    print(f"   Password : {ADMIN_PASSWORD}")
    print()
    print("⚠️  Altere a password após o primeiro login!")


if __name__ == "__main__":
    asyncio.run(main())
