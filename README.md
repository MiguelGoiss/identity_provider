# 🛡️ Serviço de Autenticação (Auth Service)

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Tortoise-ORM](https://img.shields.io/badge/Tortoise--ORM-v0.25.4-blue?style=for-the-badge)](https://tortoise.github.io/)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-316192?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)

Este é o microsserviço de **Autenticação, Identidade e Controlo de Acesso (IAM)** do ecossistema IT_Platform. Ele atua como o **Identity Provider (IdP)** centralizado para toda a plataforma, gerindo utilizadores, sessões, chaves de encriptação, controlo de acessos baseado em perfis (RBAC) e a estrutura organizacional.

---

## 🚀 Funcionalidades Principais

*   **Autenticação Flexível**: Suporta login tradicional com palavra-passe ou autenticação sem password via PIN/OTP (One-Time Password) enviado por e-mail.
*   **Emissão de Tokens JWT Assimétricos**: Emite `Access Tokens` e `Refresh Tokens` assinados com algoritmo **RS256** (RSA 2048-bit).
*   **Gateway Integrado via JWKS**: Expõe um endpoint público `/.well-known/jwks.json` contendo a chave pública. Qualquer outro microsserviço na rede (como o Gateway) pode ler e armazenar em cache a chave pública para validar de forma autónoma e sem latência a integridade e permissões dos tokens JWT.
*   **Controlo de Acesso Granular (RBAC)**: Associação de utilizadores a Perfis (*Roles*), que possuem Permissões (*Slugs*) específicas de sistema e acesso a ecrãs/janelas (`AppWindows`).
*   **Estrutura Organizacional Hierárquica**: Substituição de departamentos estáticos por uma árvore hierárquica dinâmica usando `OrgUnit` (Unidades Organizacionais) e `OrgUnitType`.
*   **Encriptação PII at Rest**: Criptografia de dados sensíveis na base de dados com blind indexation para pesquisas indexadas sem comprometer a confidencialidade (Fase 1 e 2).
*   **Comunicação Interna Protegida**: Endpoints internos sob o prefixo `/api/v1` são validados por uma chave estática no cabeçalho `X-Internal-Key`.

---

## 🛠️ Pilha Tecnológica (Tech Stack)

*   **Web Framework**: FastAPI (Assíncrono, OpenAPI nativa)
*   **Banco de Dados**: PostgreSQL 18
*   **ORM**: Tortoise ORM (Assíncrono, padrões de modelação robustos)
*   **Migrações de BD**: Aerich
*   **Criptografia**: `cryptography` (PII), `bcrypt` (hashing de passwords) e `python-jose` (geração de assinaturas e tokens JWT)

---

## 📁 Estrutura do Projeto

```text
authentication/
├── app/
│   ├── core/              # Configurações globais, leitura de variáveis de ambiente e segurança
│   ├── crypto/            # Camada de criptografia e blind index para dados sensíveis (PII)
│   ├── database/          # Configurações de BD, modelos ORM Tortoise e Repositórios
│   │   ├── models/        # Modelos relacionais (User, Company, Role, OrgUnit, etc.)
│   │   └── repository/    # Abstração de persistência (AuthRepository, etc.)
│   ├── schemas/           # Validações de entrada/saída Pydantic
│   ├── routers/           # Endpoints HTTP FastAPI agrupados por lógica de negócio
│   ├── utils/             # Utilitários (envio de e-mail, parser de queries, etc.)
│   ├── dependencies.py    # Injeção de dependências comuns (e.g. verify_internal_access)
│   └── main.py            # Inicialização, middlewares e registo do ORM
├── migrations/            # Ficheiros de migração de BD gerados pelo Aerich
├── scripts/               # Scripts utilitários de migração e sementeira de dados
├── Dockerfile             # Configuração da imagem Docker
├── docker-compose.yml     # Orquestração local do serviço e banco de dados
├── requirements.txt       # Dependências Python do projeto
└── pyproject.toml         # Configuração de ferramentas (Aerich, etc.)
```

---

## 🛠️ Configuração e Instalação Local

### 1. Pré-requisitos
*   Python 3.11 ou superior (Docker usa 3.13-slim)
*   Instância de PostgreSQL ativa ou Docker

### 2. Configurar Variáveis de Ambiente
Duplique o ficheiro `.env` ou crie uma cópia a partir de um exemplo e configure os valores:
```bash
# Exemplo de variáveis principais
DB_HOST="localhost"
DB_PORT=5432
DB_USER="db_user"
DB_PASSWORD="your-db-password"
DB_NAME="idp_db"

# Configurações de Email (Para envio de OTP)
MAIL_USERNAME="noreply"
MAIL_PASSWORD="your-mail-password"
MAIL_FROM="noreply@domain.com"
MAIL_PORT=587
MAIL_SERVER="smtp.domain.com"

# Comunicação Interna (Chave estática de Gateway/Service-to-Service)
INTERNAL_API_KEY="super_secret_long_random_string"

# Chaves Criptográficas RSA (Privada em Base64 para assinatura JWT)
AUTH_PRIVATE_KEY="super_secret_private_key"
AUTH_KEY_ID="super_secret_key_id"

# Chaves de Encriptação PII (Hexadecimal de 32 bytes)
# Estas chaves apenas se encontram aqui para o bom funcionamento da api, em produção 
# devem ser geradas e guardadas de forma segura, idealmente num KMS ou Vault.
PII_CURRENT_KEY_VERSION="v1"
PII_ENCRYPTION_KEY_V1="super_secret_encryption_key"
PII_INDEX_KEY_V1="super_secret_index_key"
```

### 3. Instalar Dependências e Correr com Ambiente Virtual (Local)
```bash
# Criar e ativar o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar pacotes
pip install -r requirements.txt

# Executar as migrações da base de dados (Aerich)
aerich upgrade

# Iniciar o servidor local (Uvicorn)
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```
O serviço estará acessível em `http://localhost:8003` e a documentação interativa Swagger em `http://localhost:8003/docs`.

### 4. Executar via Docker Compose
Se preferir utilizar a infraestrutura Dockerizada fornecida pelo `docker-compose.yml`:
```bash
# Construir e iniciar os containers (API + DB PostgreSQL)
docker-compose up --build -d

# Visualizar os logs do serviço
docker-compose logs -f api
```
Com a configuração por omissão do Compose, a API estará acessível em `http://localhost:8000`.

---

## ⚡ Scripts Utilitários Importantes

O diretório `scripts/` contém utilitários para configurar e gerir a base de dados:

### Gerar Novo Par de Chaves RSA (JWKS / JWT)
Para gerar chaves de assinatura públicas e privadas atualizadas:
```bash
python scripts/generate_keys.py
```
O output imprimirá o JSON de chaves públicas para guardar em `jwks.json` e a chave privada codificada em Base64 para colocar no `.env`.

### Criar Administrador Inicial
Para criar o utilizador administrador de sistema com todos os perfis e permissões na base de dados:
```bash
python scripts/create_admin.py
```
*   **Customizar credenciais**: Pode exportar variáveis de ambiente para definir as credenciais do admin:
    ```bash
    ADMIN_EMAIL=suporte@sistema.com ADMIN_PASSWORD=Segura123! python scripts/create_admin.py
    ```

### Executar Migrações Manuais
Para gerir esquemas de base de dados:
```bash
# Inicializar base de dados
aerich init-db

# Criar nova migração após alterar os modelos Tortoise
aerich migrate --name nome_da_alteracao

# Aplicar migrações pendentes
aerich upgrade
```

---

## 🔒 Segurança e Comunicação Externa

*   **Endpoints Públicos**:
    *   `GET /`: Health Check geral da aplicação.
    *   `GET /health`: Health Check detalhado (incluindo conexão à base de dados).
    *   `GET /.well-known/jwks.json`: Chaves públicas de assinatura para verificação de JWTs.
    *   `POST /auth/login`: Autenticação e geração de tokens.
*   **Endpoints Internos (`/api/v1/*`)**:
    *   Exigem que a chamada inclua o header `X-Internal-Key` com o valor coincidente da variável de ambiente `INTERNAL_API_KEY`. Caso contrário, será retornado `403 Forbidden`.
