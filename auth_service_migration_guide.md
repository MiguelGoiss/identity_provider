# Guia de Migração: Auth Service → Multi-App Identity Platform

> **Contexto:** FastAPI + Tortoise ORM + MySQL + python-jose (RS256) + bcrypt  
> Este documento cobre todas as alterações necessárias para transformar o serviço de autenticação actual num identity provider reutilizável por múltiplas aplicações, com gestão hierárquica organizacional dinâmica.

---

## 1. Visão Geral das Alterações

| Área | Estado Actual | Estado Final |
|---|---|---|
| Hierarquia organizacional | `Department`, `Local` fixos | `OrgUnitType` + `OrgUnit` (árvore dinâmica) |
| Controlo de acesso a apps | Não existe | `Application` + `UserApplicationAccess` |
| RBAC | `Role`/`Permission` genéricos | Scoped ao auth service apenas |
| JWT payload | Permissões + department_id | Identidade + org_unit + apps autorizadas |
| Endpoint `/me` | Devolve utilizador | Devolve utilizador + apps + hierarquia |
| `/refresh-token` | Valida e renova | Valida estado + revoga se desactivado |

---

## 2. Alterações ao Schema de Base de Dados

### 2.1. Novas tabelas a criar

#### `org_unit_types`

```python
# app/database/models/org_unit_type.py
from tortoise import fields
from tortoise.models import Model


class OrgUnitType(Model):
    id: int = fields.IntField(pk=True)
    name: str = fields.CharField(max_length=100, unique=True)
    level: int = fields.IntField()
    # 0 = topo (ex: Empresa), 1 = Direcção, 2 = Departamento, 3 = Secção...
    # Apenas informativo — a hierarquia real é definida pelo parent_id em OrgUnit

    class Meta:
        table = "org_unit_types"
        ordering = ["level"]
```

#### `org_units`

```python
# app/database/models/org_unit.py
from __future__ import annotations
from tortoise import fields
from tortoise.models import Model


class OrgUnit(Model):
    id: int = fields.IntField(pk=True)
    name: str = fields.CharField(max_length=150)
    type: fields.ForeignKeyRelation[OrgUnitType] = fields.ForeignKeyField(
        "models.OrgUnitType", related_name="units"
    )
    company: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.Company", related_name="org_units"
    )
    parent: fields.ForeignKeyRelation[OrgUnit] | None = fields.ForeignKeyField(
        "models.OrgUnit",
        null=True,
        blank=True,
        related_name="children",
    )
    is_active: bool = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "org_units"
```

#### `applications`

```python
# app/database/models/application.py
from tortoise import fields
from tortoise.models import Model


class Application(Model):
    id: int = fields.IntField(pk=True)
    slug: str = fields.CharField(max_length=50, unique=True)
    # ex: "helpdesk", "hrm", "contabilidade"
    name: str = fields.CharField(max_length=100)
    is_active: bool = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "applications"
```

#### `user_application_access`

```python
# app/database/models/user_application_access.py
from tortoise import fields
from tortoise.models import Model


class UserApplicationAccess(Model):
    id: int = fields.IntField(pk=True)
    user: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.User", related_name="app_accesses"
    )
    application: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.Application", related_name="user_accesses"
    )
    granted_at = fields.DatetimeField(auto_now_add=True)
    granted_by: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.User", related_name="granted_accesses"
    )

    class Meta:
        table = "user_application_access"
        unique_together = (("user", "application"),)
```

---

### 2.2. Alterações ao modelo `User` existente

Remover as FK directas para `Department` e `Local`. Substituir por `OrgUnit` e adicionar `job_title`:

```python
# app/database/models/user.py — campos a ALTERAR/ADICIONAR

# REMOVER:
# department: fields.ForeignKeyRelation[Department] = fields.ForeignKeyField(...)
# local: fields.ForeignKeyRelation[Local] = fields.ForeignKeyField(...)

# ADICIONAR:
org_unit: fields.ForeignKeyRelation | None = fields.ForeignKeyField(
    "models.OrgUnit",
    null=True,
    blank=True,
    related_name="users",
)
job_title: str | None = fields.CharField(max_length=100, null=True, blank=True)
# ex: "Adjunto de Direcção", "Assessor", "Técnico Superior"
```

> **Nota de migração:** Antes de remover `department` e `local`, cria os `OrgUnitType` e `OrgUnit` correspondentes e faz a migração de dados. Script de exemplo na secção 6.

---

### 2.3. Tabelas a remover (após migração de dados)

- `departments` → substituída por `org_units` com `OrgUnitType.name = "Departamento"`
- `locals` → substituída por `org_units` com `OrgUnitType.name = "Local"`

As entidades `Role`, `Permission` e `AppWindow` **mantêm-se**, mas o seu scope passa a ser exclusivamente para gestão do próprio auth service (quem pode criar utilizadores, gerir empresas, etc.).

---

## 3. Alterações ao JWT Payload

### Antes

```json
{
  "sub": "uuid",
  "company_id": 3,
  "department_id": 12,
  "permissions": ["user:edit", "role:create"]
}
```

### Depois

```json
{
  "sub": "uuid",
  "employee_number": "EMP-001",
  "company_id": 3,
  "org_unit_id": 47,
  "org_unit_type": "Departamento",
  "job_title": "Adjunto de Direcção",
  "is_agent": true,
  "apps": ["helpdesk", "hrm", "contabilidade"]
}
```

**Regras:**
- `permissions` saem do JWT — deixam de ser transportadas para apps externas.
- `apps` é a lista de slugs das aplicações a que o utilizador tem acesso activo.
- As permissões do auth service (RBAC interno) continuam a ser validadas, mas apenas em endpoints do próprio auth service, não propagadas para fora.

### Alteração na função de geração de token

```python
# app/core/security.py (ou onde estiver a lógica de criação do JWT)
from app.database.models.user_application_access import UserApplicationAccess


async def create_access_token(user: User) -> str:
    apps = await UserApplicationAccess.filter(
        user=user,
        application__is_active=True,
    ).values_list("application__slug", flat=True)

    org_unit = await user.org_unit.first() if user.org_unit_id else None

    payload = {
        "sub": str(user.id),
        "employee_number": user.employee_number,
        "company_id": user.company_id,        # manter se já existe
        "org_unit_id": org_unit.id if org_unit else None,
        "org_unit_type": (await org_unit.type).name if org_unit else None,
        "job_title": user.job_title,
        "is_agent": user.is_agent,
        "apps": list(apps),
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.AUTH_PRIVATE_KEY, algorithm="RS256")
```

---

## 4. Alterações aos Endpoints Existentes

### 4.1. `/me` — adicionar apps e org_unit

```python
# app/routers/auth.py

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    # Vai sempre à BD — nunca serve dados do JWT em cache
    user = await User.get_or_none(
        id=current_user.id,
        deactivated_at=None,
        deleted_at=None,
    ).prefetch_related("org_unit__type")

    if not user:
        raise HTTPException(status_code=401, detail="Account deactivated")

    apps = await UserApplicationAccess.filter(
        user=user,
        application__is_active=True,
    ).values_list("application__slug", flat=True)

    return {
        "user": user,
        "org_unit": await user.org_unit if user.org_unit_id else None,
        "apps": list(apps),
    }
```

### 4.2. `/refresh-token` — validar estado e acesso

```python
@router.post("/refresh-token")
async def refresh_token(refresh_token: str = Body(...)):
    payload = verify_token(refresh_token)  # valida assinatura RS256

    user = await User.get_or_none(
        id=payload["sub"],
        deactivated_at=None,
        deleted_at=None,
    )
    if not user:
        raise HTTPException(status_code=401, detail="User deactivated or not found")

    # Emite novo access token com apps actualizadas
    new_access_token = await create_access_token(user)
    return {"access_token": new_access_token}
```

> **Efeito:** Se o utilizador for desactivado no auth service, o próximo `/refresh-token` devolve 401 em todas as apps simultaneamente — sem necessidade de broker de eventos.

---

## 5. Novos Endpoints a Criar

### 5.1. Gestão de `OrgUnitType` (protegido por RBAC interno)

```
POST   /api/v1/org-unit-types        → criar tipo (ex: "Equipa")
GET    /api/v1/org-unit-types        → listar tipos
DELETE /api/v1/org-unit-types/{id}   → remover tipo
```

### 5.2. Gestão de `OrgUnit` (protegido por RBAC interno)

```
POST   /api/v1/org-units             → criar unidade
GET    /api/v1/org-units             → listar (com filtro company_id, parent_id)
GET    /api/v1/org-units/{id}/tree   → árvore completa a partir desta unidade
PATCH  /api/v1/org-units/{id}        → editar
DELETE /api/v1/org-units/{id}        → desactivar (soft delete)
```

#### Endpoint `/tree` com CTE recursiva (raw SQL via Tortoise)

```python
# app/database/repository/org_unit_repository.py
from tortoise import Tortoise


async def get_org_unit_tree(root_id: int) -> list[dict]:
    conn = Tortoise.get_connection("default")
    query = """
        WITH RECURSIVE hierarchy AS (
            SELECT
                ou.id, ou.name, ou.parent_id, out.name AS type_name, 0 AS depth
            FROM org_units ou
            JOIN org_unit_types out ON ou.type_id = out.id
            WHERE ou.id = %s AND ou.is_active = TRUE

            UNION ALL

            SELECT
                ou.id, ou.name, ou.parent_id, out.name AS type_name, h.depth + 1
            FROM org_units ou
            JOIN org_unit_types out ON ou.type_id = out.id
            INNER JOIN hierarchy h ON ou.parent_id = h.id
            WHERE ou.is_active = TRUE
        )
        SELECT * FROM hierarchy ORDER BY depth, name;
    """
    results = await conn.execute_query_dict(query, [root_id])
    return results
```

### 5.3. Gestão de `Application` (protegido por RBAC interno)

```
POST   /api/v1/applications          → registar nova app
GET    /api/v1/applications          → listar apps
PATCH  /api/v1/applications/{id}     → editar / desactivar
```

### 5.4. Gestão de acesso de utilizadores a apps

```
POST   /api/v1/users/{user_id}/app-access          → conceder acesso
DELETE /api/v1/users/{user_id}/app-access/{app_id} → revogar acesso
GET    /api/v1/users/{user_id}/app-access          → listar acessos
```

### 5.5. Endpoint interno para apps externas (protegido por `X-Internal-Key`)

```python
# Permite que uma app externa resolva a hierarquia completa de um utilizador
# sem expor este endpoint publicamente

GET /internal/users/{user_uid}/org-tree
# Header obrigatório: X-Internal-Key: <INTERNAL_API_KEY>
# Resposta: árvore da org_unit do utilizador até ao topo
```

---

## 6. Script de Migração de Dados

Antes de apagar `departments` e `locals`, migrar para `org_units`:

```python
# scripts/migrate_org_structure.py
# Executar uma vez, manualmente, após criar as novas tabelas via Aerich

import asyncio
from tortoise import Tortoise
from app.core.config import settings


async def migrate():
    await Tortoise.init(config=settings.TORTOISE_ORM)

    # 1. Criar OrgUnitTypes base
    from app.database.models.org_unit_type import OrgUnitType
    empresa_type, _  = await OrgUnitType.get_or_create(name="Empresa",     defaults={"level": 0})
    dept_type, _     = await OrgUnitType.get_or_create(name="Departamento", defaults={"level": 1})
    local_type, _    = await OrgUnitType.get_or_create(name="Local",        defaults={"level": 2})

    # 2. Migrar Departments → OrgUnit
    from app.database.models.department import Department
    from app.database.models.org_unit import OrgUnit

    departments = await Department.all().prefetch_related("company")
    dept_map: dict[int, int] = {}  # department.id → org_unit.id

    for dept in departments:
        ou = await OrgUnit.create(
            name=dept.name,
            type=dept_type,
            company=dept.company,
            parent=None,
            is_active=True,
        )
        dept_map[dept.id] = ou.id

    # 3. Migrar Locals → OrgUnit (filho do Departamento correspondente)
    from app.database.models.local import Local
    locals_ = await Local.all().prefetch_related("company")

    for local in locals_:
        await OrgUnit.create(
            name=local.name,
            type=local_type,
            company=local.company,
            parent_id=dept_map.get(local.department_id),
            is_active=True,
        )

    # 4. Actualizar User.org_unit com o OrgUnit correspondente ao seu Department
    from app.database.models.user import User
    users = await User.all()
    for user in users:
        if user.department_id and user.department_id in dept_map:
            user.org_unit_id = dept_map[user.department_id]
            await user.save(update_fields=["org_unit_id"])

    print("Migração concluída.")
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(migrate())
```

---

## 7. Alterações ao Aerich (Migrações de Schema)

Ordem recomendada para evitar erros de FK:

```bash
# 1. Criar as novas tabelas (sem ainda remover as antigas)
aerich migrate --name add_org_units_and_applications

# 2. Executar o script de migração de dados
python scripts/migrate_org_structure.py

# 3. Remover FK antigas do modelo User (department, local)
aerich migrate --name remove_legacy_org_fields

# 4. (Opcional, após validação) Dropar tabelas departments e locals
aerich migrate --name drop_legacy_org_tables
```

---

## 8. Alterações às Pydantic Schemas

### Novo schema de resposta do `/me`

```python
# app/schemas/auth.py
from pydantic import BaseModel


class OrgUnitOut(BaseModel):
    id: int
    name: str
    type_name: str
    parent_id: int | None

    class Config:
        from_attributes = True


class MeResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    username: str
    employee_number: str
    job_title: str | None
    is_agent: bool
    org_unit: OrgUnitOut | None
    apps: list[str]  # slugs das apps autorizadas
```

---

## 9. Checklist de Implementação

- [ ] Criar modelos `OrgUnitType`, `OrgUnit`, `Application`, `UserApplicationAccess`
- [ ] Alterar modelo `User`: adicionar `org_unit`, `job_title`; remover `department`, `local`
- [ ] Gerar migração Aerich para novas tabelas
- [ ] Executar script de migração de dados
- [ ] Gerar migração Aerich para remoção de campos legacy
- [ ] Actualizar `create_access_token` — novo payload JWT
- [ ] Actualizar endpoint `/me` — validação BD + apps
- [ ] Actualizar endpoint `/refresh-token` — validação de estado
- [ ] Criar routers para `OrgUnitType`, `OrgUnit`, `Application`, `UserApplicationAccess`
- [ ] Criar endpoint interno `/internal/users/{uid}/org-tree` protegido por `X-Internal-Key`
- [ ] Actualizar Pydantic schemas
- [ ] Actualizar JWKS — garantir `kid` no header dos tokens para suportar rotação futura
- [ ] Testar propagação de desactivação via `/refresh-token`
- [ ] Testar revogação de acesso a app via `/refresh-token`
