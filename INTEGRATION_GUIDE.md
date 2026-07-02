# Guia de Integração: Auth Service (Identity Provider)

> **Stack:** FastAPI · Tortoise ORM · PostgreSQL · RS256 (JWT assimétrico) · bcrypt  
> **Versão do serviço:** `0.9.0`

Este documento destina-se a programadores que necessitem de integrar microsserviços ou aplicações externas com o **Auth Service**. O serviço funciona como um **Identity Provider (IdP)** centralizado: emite e assina JWTs, gere utilizadores, estrutura organizacional e acessos a aplicações.

---

## 1. Visão Geral da Arquitetura

```
┌─────────────┐    credenciais    ┌─────────────────┐
│   Frontend  │ ───────────────→  │   Auth Service  │
│   / Client  │ ←─── JWT ───────  │  (IdP)          │
└─────────────┘                   └────────┬────────┘
                                           │  /.well-known/jwks.json
       ┌───────────────────────────────────┘
       ↓
┌──────────────┐    Authorization: Bearer <token>    ┌──────────────┐
│   Frontend   │ ──────────────────────────────────→ │  Microsserv. │
│              │                                     │  (Helpdesk,  │
└──────────────┘                                     │   RH, etc.)  │
                                                     └──────┬───────┘
                                                            │ valida token
                                                            │ localmente
                                                            │ (sem BD central)
                                                            ▼
                                                     ┌──────────────┐
                                                     │  Public Key  │
                                                     │  (JWKS)      │
                                                     └──────────────┘
```

**Princípio fundamental:** O Auth Service **assina** os tokens com uma RSA Private Key. Os microsserviços **validam** a assinatura localmente usando a Public Key exposta via JWKS — sem contactar a base de dados central a cada pedido.

---

## 2. Fluxo de Autenticação

### 2.1. Identificação do Utilizador (pré-login)

Antes do login propriamente dito, o cliente deve determinar o método de autenticação do utilizador:

```http
POST /auth/.validate-identifier
Content-Type: application/json

{"username": "utilizador@empresa.com"}
```

**Resposta:**
```json
{
  "is_agent":       true,
  "is_user":        true,
  "is_collaborator": false
}
```

| Campo | Significado |
|---|---|
| `is_agent: true` | Utilizador tem password — usar fluxo de login normal |
| `is_collaborator: true` | Utilizador sem password — um OTP de 6 dígitos foi enviado para o email associado |

> **Nota de segurança:** Se o utilizador não existir, a resposta é idêntica à de um colaborador (user enumeration mitigation).

### 2.2. Login

```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded
X-App-Client: helpdesk   ← (opcional) slug da aplicação cliente

username=utilizador@empresa.com&password=<password_ou_otp>
```

**Resposta (200 OK):**
```json
{
  "access_token":  "<JWT>",
  "refresh_token": "<JWT>",
  "token_type":    "bearer"
}
```

**Códigos de erro:**

| HTTP | Detalhe |
|---|---|
| `401` | Credenciais inválidas ou OTP errado |
| `403` | Conta desativada |
| `419` | Credenciais incorretas (resposta ambígua para segurança) |

O header `X-App-Client` (slug da aplicação, ex: `"helpdesk"`) é **recomendado** — permite que o serviço registe a sessão associada à aplicação correta.

### 2.3. Renovação do Token (Refresh)

O access token expira em **15 minutos** por defeito. Para renovar sem re-autenticar:

```http
POST /auth/refresh
Content-Type: application/json
X-App-Client: helpdesk   ← (opcional)

{"refresh_token": "<refresh_JWT>"}
```

**Comportamento:**
- Valida a assinatura RS256 do refresh token.
- Verifica se o utilizador está ativo (`deactivated_at IS NULL`, `deleted_at IS NULL`).
- Verifica se a sessão associada ao `jti` não foi revogada.
- **Invalida** a sessão atual (rotation) e emite um novo par de tokens com um novo `jti`.

> **Efeito de segurança:** Se um utilizador for desativado no Auth Service, o próximo `/auth/refresh` devolve `401` em **todas as aplicações simultaneamente** — sem necessidade de mensageria ou eventos.

### 2.4. Logout

```http
POST /auth/logout
Content-Type: application/json

{"refresh_token": "<refresh_JWT>"}
```

Revoga a sessão associada ao `jti` do token. Sempre devolve `200` (mesmo que o token já esteja inválido).

---

## 3. O Payload do JWT

Os tokens são assinados com **RS256** e incluem o header `kid` para suporte a rotação de chaves.

### Access Token

```json
{
  "sub":             "42",
  "uuid":            "b2f6b39d-4819-4841-b847-8fbdfa352843",
  "first_name":      "João",
  "last_name":       "Silva",
  "full_name":       "João Silva",
  "employee_number": "EMP-001",
  "company_id":      3,
  "org_unit_id":     47,
  "org_unit_type":   "Departamento",
  "job_title":       "Adjunto de Direcção",
  "apps":            ["helpdesk", "hrm", "contabilidade"],
  "exp":             1735689600,
  "jti":             "a1b2c3d4e5f6...",
  "type":            "access"
}
```

### Refresh Token

```json
{
  "sub":             "42",
  "uuid":            "b2f6b39d-4819-4841-b847-8fbdfa352843",
  "first_name":      "João",
  "last_name":       "Silva",
  "full_name":       "João Silva",
  "employee_number": "EMP-001",
  "exp":             1736294400,
  "jti":             "a1b2c3d4e5f6...",
  "type":            "refresh"
}
```

### Campos do Access Token — Referência

| Campo | Tipo | Descrição |
|---|---|---|
| `sub` | `string` | ID interno do utilizador (inteiro como string). Usar como FK interna se necessário. |
| `uuid` | `string (UUID)` | **Identificador público e estável do utilizador.** Usar como referência entre serviços. |
| `apps` | `list[string]` | Slugs das aplicações a que o utilizador tem acesso ativo. **Validar sempre antes de autorizar.** |
| `org_unit_id` | `int \| null` | ID da unidade organizacional do utilizador. |
| `org_unit_type` | `string \| null` | Tipo da unidade (ex: `"Departamento"`, `"Secção"`). |
| `company_id` | `int \| null` | ID da empresa principal do utilizador. |
| `job_title` | `string \| null` | Cargo do utilizador na empresa principal. |
| `jti` | `string` | JWT ID único — identifica a sessão. Usado para revogação. |
| `type` | `string` | `"access"` ou `"refresh"`. **Validar obrigatoriamente** para evitar usar refresh tokens como access tokens. |

> **Importante:** Usar sempre `uuid` (não `sub`) para referenciar o utilizador em bases de dados de outros serviços. O `sub` é um ID interno do Auth Service.

---

## 4. Validação do Token no Microsserviço

### 4.1. Obter a Chave Pública (JWKS)

```http
GET /.well-known/jwks.json
```

Não requer autenticação. A resposta contém a(s) chave(s) pública(s) ativas:

```json
{
  "keys": [
    {
      "kty": "RSA",
      "use": "sig",
      "kid": "auth-key-1",
      "n": "...",
      "e": "AQAB"
    }
  ]
}
```

**Estratégia de cache recomendada:**
1. Fazer download das chaves no arranque do serviço e guardar em memória.
2. Em caso de falha de validação de um token (`JWTError`), tentar refrescar a cache uma vez.
3. Nunca fazer um pedido HTTP por cada validação de token.

### 4.2. Implementação em Python (FastAPI)

```bash
pip install python-jose[cryptography] httpx
```

```python
import httpx
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()

AUTH_JWKS_URL = "http://auth-service:8003/.well-known/jwks.json"

# Cache em memória das chaves públicas
_jwks_cache: dict | None = None


async def get_jwks(force_refresh: bool = False) -> dict:
    global _jwks_cache
    if not _jwks_cache or force_refresh:
        async with httpx.AsyncClient() as client:
            response = await client.get(AUTH_JWKS_URL, timeout=5.0)
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    token = credentials.credentials
    try:
        jwks = await get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except JWTError:
        # Tentar refrescar a cache uma vez (key rotation)
        try:
            jwks = await get_jwks(force_refresh=True)
            payload = jwt.decode(
                token,
                jwks,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado",
            )

    # Garantir que é um access token, não um refresh token
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido",
        )

    return payload


def require_app(app_slug: str):
    """Dependência de autorização — valida se o utilizador tem acesso à app."""
    async def _checker(payload: dict = Depends(get_current_user)) -> dict:
        if app_slug not in payload.get("apps", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Sem acesso à aplicação: {app_slug}",
            )
        return payload
    return _checker
```

**Uso nas rotas:**

```python
from fastapi import APIRouter, Depends

router = APIRouter()

require_helpdesk = Depends(require_app("helpdesk"))

@router.get("/tickets", dependencies=[require_helpdesk])
async def list_tickets(payload: dict = Depends(get_current_user)):
  user_uuid = payload["uuid"]  # Usar UUID, não 'sub'
  # ...
  return {"user": user_uuid, "tickets": []}
```

### 4.3. Implementação em Node.js / TypeScript

```bash
npm install jose
```

```typescript
import { createRemoteJWKSet, jwtVerify } from "jose";

const JWKS = createRemoteJWKSet(
  new URL("http://auth-service:8003/.well-known/jwks.json")
);

export async function verifyToken(token: string) {
  const { payload } = await jwtVerify(token, JWKS, {
    algorithms: ["RS256"],
  });

  if (payload["type"] !== "access") {
    throw new Error("Tipo de token inválido");
  }

  const apps = payload["apps"] as string[];
  if (!apps.includes("helpdesk")) {
    throw new Error("Sem acesso à aplicação");
  }

  return payload;
}
```

---

## 5. Endpoint `/auth/me`

Para obter dados frescos do utilizador autenticado (vai sempre à base de dados):

```http
GET /auth/me
Authorization: Bearer <access_token>
```

**Resposta (200 OK):**
```json
{
  "id":              "42",
  "uuid":            "b2f6b39d-4819-4841-b847-8fbdfa352843",
  "first_name":      "João",
  "last_name":       "Silva",
  "username":        "utilizador@empresa.com",
  "employee_number": "EMP-001",
  "job_title":       "Adjunto de Direcção",
  "org_unit": {
    "id":        47,
    "name":      "Departamento de TI",
    "type_name": "Departamento",
    "parent_id": 12
  },
  "apps": ["helpdesk", "hrm"]
}
```

> **Nota:** O `employee_number` está encriptado em repouso (AES-256-GCM). O valor aqui já vem desencriptado.

---

## 6. Comunicação Servidor-para-Servidor (S2S)

Para comunicação direta entre microsserviços com o Auth Service (backend-to-backend), todos os endpoints sob `/api/v1/...` (gestão interna) e `/internal/` exigem o header:

```http
X-Internal-Key: <SERVICE_API_KEY>
```

O sistema utiliza agora **Service API Keys** geridas dinamicamente pelo Auth Service. As chaves começam pelo prefixo `sak_` e podem ter escopos associados (ex: `internal:admin`).

**Nunca expor a Service API Key no frontend.**

### 6.1. Obter a Árvore Organizacional Ascendente de um Utilizador

Permite que um microsserviço resolva toda a cadeia de chefia de um utilizador (do seu OrgUnit até à raiz):

```http
GET /internal/users/{user_id}/org-tree
X-Internal-Key: <SERVICE_API_KEY>
```

> **Nota:** O `{user_id}` é o campo `sub` do JWT (ID interno). O `uuid` do JWT não é usado aqui.

**Resposta (200 OK):**
```json
{
  "user_id": 42,
  "org_unit_ancestors": [
    {"id": 47, "name": "Departamento de TI",  "parent_id": 12, "type_name": "Departamento", "depth": 0},
    {"id": 12, "name": "Direcção de Sistemas", "parent_id": 1, "type_name": "Direcção",     "depth": 1},
    {"id": 1,  "name": "Empresa Central",      "parent_id": null, "type_name": "Empresa",   "depth": 2}
  ]
}
```

### 6.2. Aceder à API de Gestão (apenas backends internos)

Todos os endpoints de gestão requerem `X-Internal-Key`. Exemplos:

```
# Gestão de utilizadores
GET    /api/v1/users
GET    /api/v1/users/{id}

# Gestão de unidades organizacionais
GET    /api/v1/org-unit-types
GET    /api/v1/org-units
GET    /api/v1/org-units/{id}/tree

# Gestão de aplicações registadas
GET    /api/v1/applications

# Gestão de acessos do utilizador a apps
GET    /api/v1/users/{user_id}/app-access
POST   /api/v1/users/{user_id}/app-access    ← conceder acesso
DELETE /api/v1/users/{user_id}/app-access/{app_id} ← revogar acesso
```

---

## 7. Registar uma Nova Aplicação no IdP

Para que os utilizadores possam ter acesso à sua aplicação (slug no campo `apps` do JWT), é necessário registar a aplicação no Auth Service e atribuir acessos:

**Passo 1 — Registar a aplicação:**
```http
POST /api/v1/applications
X-Internal-Key: <INTERNAL_API_KEY>
Content-Type: application/json

{
  "slug": "minha-app",
  "name": "Minha Aplicação"
}
```

**Passo 2 — Conceder acesso a um utilizador:**
```http
POST /api/v1/users/{user_id}/app-access
X-Internal-Key: <INTERNAL_API_KEY>
Content-Type: application/json

{
  "application_id": <id_da_aplicacao>
}
```

A partir do próximo login ou refresh token, o slug `"minha-app"` aparecerá no campo `apps` do JWT desse utilizador.

**Passo 3 — Validar no seu serviço:**
```python
require_minha_app = Depends(require_app("minha-app"))
```

---

## 8. Modelo de Dados Relevante

```
User
 ├─ uuid          (identificador público estável — usar entre serviços)
 ├─ org_unit      → OrgUnit
 │                     ├─ type → OrgUnitType (ex: "Departamento", "Secção")
 │                     └─ parent → OrgUnit (hierarquia recursiva)
 ├─ companies     → UserCompany (M2M com Company)
 │                     ├─ is_primary
 │                     ├─ job_title
 │                     └─ employee_number (encriptado em repouso)
 ├─ identities    → UserIdentity (ex: username, email — encriptados em repouso)
 ├─ profile       → PersonProfile (first_name, last_name, full_name)
 ├─ app_accesses  → UserApplicationAccess → Application (slug)
 └─ auth_sessions → AuthSession (jti, revoked_at, ip_address, user_agent)
```

---

## 9. Variáveis de Ambiente Necessárias no Microsserviço Integrador

```env
# URL interna do Auth Service (dentro da rede Docker/K8s)
AUTH_SERVICE_URL=http://authentication:8003

# Chave gerada no Auth Service para comunicação S2S (formato sak_...)
INTERNAL_API_KEY=sak_1234567890abcdef...
```

---

## 10. Boas Práticas e Recomendações

| # | Recomendação |
|---|---|
| ✅ | **Usar `uuid`** do token para referenciar utilizadores entre serviços, nunca `sub`. |
| ✅ | **Validar `type: "access"`** antes de aceitar o token — impede uso de refresh tokens. |
| ✅ | **Validar `apps`** antes de executar qualquer ação — o token sozinho não garante acesso à sua app. |
| ✅ | **Cache do JWKS** em memória com refresh lazy em caso de erro de validação. |
| ✅ | **Não armazenar dados completos do utilizador** — guardar apenas o `uuid` e dados específicos do domínio. |
| ✅ | **Não validar estado da conta a cada pedido** — a revogação é propagada no próximo refresh. |
| ✅ | **Usar `X-App-Client`** no login e refresh para melhor rastreabilidade de sessões. |
| ❌ | Nunca expor o `INTERNAL_API_KEY` no frontend ou em logs. |
| ❌ | Nunca fazer pedidos ao `/jwks.json` por cada validação de token. |
| ❌ | Nunca confiar no conteúdo do token sem verificar a assinatura RS256. |

---

## 11. Referência Rápida de Endpoints

| Método | Endpoint | Auth | Descrição |
|---|---|---|---|
| `POST` | `/auth/.validate-identifier` | Pública | Determina o método de login do utilizador |
| `POST` | `/auth/login` | Pública | Emite access + refresh token |
| `POST` | `/auth/refresh` | Pública (refresh token) | Renova tokens (session rotation) |
| `POST` | `/auth/logout` | Pública (refresh token) | Revoga a sessão |
| `GET`  | `/auth/me` | Bearer (access token) | Dados atuais do utilizador autenticado |
| `GET`  | `/.well-known/jwks.json` | Pública | Chaves públicas para validação de tokens |
| `GET`  | `/internal/users/{id}/org-tree` | `X-Internal-Key` | Árvore organizacional do utilizador |
| `*`    | `/api/v1/...` | `X-Internal-Key` | API de gestão (S2S apenas) |
| `*`    | `/api/v1/service-api-keys` | Bearer (`api_key:manage`) | Gestão das Service API Keys |
| `GET`  | `/health` | Pública | Health check do serviço |
