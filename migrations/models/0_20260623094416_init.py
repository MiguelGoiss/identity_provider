from tortoise import BaseDBAsyncClient

RUN_IN_TRANSACTION = True


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "app_windows" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL,
    "slug" VARCHAR(100) NOT NULL UNIQUE,
    "icon" VARCHAR(50),
    "order" INT NOT NULL DEFAULT 0,
    "parent_id" INT REFERENCES "app_windows" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "applications" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "slug" VARCHAR(50) NOT NULL UNIQUE,
    "name" VARCHAR(100) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True
);
CREATE TABLE IF NOT EXISTS "company" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255) NOT NULL,
    "acronym" VARCHAR(15) UNIQUE,
    "deactivated_at" TIMESTAMPTZ
);
CREATE TABLE IF NOT EXISTS "contact_types" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "slug" VARCHAR(50) NOT NULL UNIQUE,
    "label" VARCHAR(100) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True
);
CREATE TABLE IF NOT EXISTS "local" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(155) NOT NULL,
    "short" VARCHAR(15) NOT NULL,
    "background" VARCHAR(15),
    "text" VARCHAR(15),
    "company_id" INT NOT NULL REFERENCES "company" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "org_unit_types" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL UNIQUE,
    "level" INT NOT NULL
);
CREATE TABLE IF NOT EXISTS "org_units" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(150) NOT NULL,
    "is_active" BOOL NOT NULL DEFAULT True,
    "company_id" INT NOT NULL REFERENCES "company" ("id") ON DELETE CASCADE,
    "parent_id" INT REFERENCES "org_units" ("id") ON DELETE CASCADE,
    "type_id" INT NOT NULL REFERENCES "org_unit_types" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "permission" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "slug" VARCHAR(100) NOT NULL UNIQUE,
    "description" TEXT NOT NULL,
    "app_window_id" INT REFERENCES "app_windows" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "role" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(100) NOT NULL,
    "company_id" INT REFERENCES "company" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "users" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "uuid" UUID NOT NULL UNIQUE,
    "hashed_password" VARCHAR(255),
    "recovery_secret" VARCHAR(255),
    "recovery_secret_expires_at" TIMESTAMPTZ,
    "recovery_attempts" INT NOT NULL DEFAULT 0,
    "deactivated_at" TIMESTAMPTZ,
    "deleted_at" TIMESTAMPTZ,
    "last_time_seen" TIMESTAMPTZ,
    "extra_info" TEXT
);
CREATE INDEX IF NOT EXISTS "idx_users_uuid_03721e" ON "users" ("uuid");
CREATE TABLE IF NOT EXISTS "auth_sessions" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "jti" VARCHAR(255) NOT NULL UNIQUE,
    "issued_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "expires_at" TIMESTAMPTZ NOT NULL,
    "revoked_at" TIMESTAMPTZ,
    "ip_address" VARCHAR(45),
    "user_agent" VARCHAR(512),
    "application_id" INT REFERENCES "applications" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_auth_sessio_jti_d7655b" ON "auth_sessions" ("jti");
CREATE TABLE IF NOT EXISTS "person_contacts" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "description" VARCHAR(255),
    "is_public" BOOL NOT NULL DEFAULT False,
    "is_primary" BOOL NOT NULL DEFAULT False,
    "is_verified" BOOL NOT NULL DEFAULT False,
    "verified_at" TIMESTAMPTZ,
    "scope" VARCHAR(20) NOT NULL DEFAULT 'personal',
    "value_enc" TEXT,
    "value_idx" VARCHAR(64),
    "value_key_version" SMALLINT NOT NULL DEFAULT 1,
    "contact_type_id" INT NOT NULL REFERENCES "contact_types" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_person_cont_value_i_87d4cc" ON "person_contacts" ("value_idx");
CREATE TABLE IF NOT EXISTS "person_emails" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_primary" BOOL NOT NULL DEFAULT False,
    "is_verified" BOOL NOT NULL DEFAULT False,
    "verified_at" TIMESTAMPTZ,
    "scope" VARCHAR(20) NOT NULL DEFAULT 'personal',
    "email_enc" TEXT,
    "email_idx" VARCHAR(64),
    "email_key_version" SMALLINT NOT NULL DEFAULT 1,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_person_emai_user_id_2c2cbf" UNIQUE ("user_id", "email_idx")
);
CREATE INDEX IF NOT EXISTS "idx_person_emai_email_i_ab073f" ON "person_emails" ("email_idx");
CREATE TABLE IF NOT EXISTS "person_profiles" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "first_name" VARCHAR(100) NOT NULL,
    "last_name" VARCHAR(100) NOT NULL,
    "preferred_name" VARCHAR(100),
    "locale" VARCHAR(10) NOT NULL DEFAULT 'pt-PT',
    "time_zone" VARCHAR(50) NOT NULL DEFAULT 'Europe/Lisbon',
    "photo_uri" VARCHAR(255),
    "full_name_enc" TEXT,
    "full_name_idx" VARCHAR(64),
    "full_name_key_version" SMALLINT NOT NULL DEFAULT 1,
    "tax_id_enc" TEXT,
    "tax_id_idx" VARCHAR(64) UNIQUE,
    "tax_id_key_version" SMALLINT NOT NULL DEFAULT 1,
    "birth_date_enc" TEXT,
    "birth_date_key_version" SMALLINT NOT NULL DEFAULT 1,
    "user_id" INT NOT NULL UNIQUE REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_person_prof_full_na_c3a2c8" ON "person_profiles" ("full_name_idx");
CREATE INDEX IF NOT EXISTS "idx_person_prof_tax_id__b93d95" ON "person_profiles" ("tax_id_idx");
CREATE TABLE IF NOT EXISTS "service_api_keys" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "uuid" UUID NOT NULL UNIQUE,
    "name" VARCHAR(255) NOT NULL,
    "service_name" VARCHAR(255) NOT NULL,
    "environment" VARCHAR(50) NOT NULL,
    "key_prefix" VARCHAR(12) NOT NULL UNIQUE,
    "key_hash" VARCHAR(64) NOT NULL,
    "status" VARCHAR(50) NOT NULL DEFAULT 'active',
    "scopes" JSONB NOT NULL,
    "last_used_at" TIMESTAMPTZ,
    "last_used_ip" VARCHAR(45),
    "expires_at" TIMESTAMPTZ,
    "revoked_at" TIMESTAMPTZ,
    "revocation_reason" TEXT,
    "created_by_user_id" INT REFERENCES "users" ("id") ON DELETE CASCADE,
    "revoked_by_user_id" INT REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_service_api_uuid_7b00be" ON "service_api_keys" ("uuid");
CREATE INDEX IF NOT EXISTS "idx_service_api_key_pre_3789ae" ON "service_api_keys" ("key_prefix");
CREATE TABLE IF NOT EXISTS "api_key_audit_logs" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "api_key_uuid" UUID NOT NULL,
    "event_type" VARCHAR(50) NOT NULL,
    "performed_by_service" VARCHAR(255),
    "ip_address" VARCHAR(45),
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "metadata" JSONB,
    "api_key_id" INT NOT NULL REFERENCES "service_api_keys" ("id") ON DELETE CASCADE,
    "performed_by_user_id" INT REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "user_application_access" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "granted_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "application_id" INT NOT NULL REFERENCES "applications" ("id") ON DELETE CASCADE,
    "granted_by_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_applic_user_id_4e1681" UNIQUE ("user_id", "application_id")
);
CREATE TABLE IF NOT EXISTS "user_companies" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "is_primary" BOOL NOT NULL DEFAULT False,
    "job_title" VARCHAR(100),
    "admission_date" DATE,
    "termination_date" DATE,
    "employment_type" VARCHAR(50),
    "status" VARCHAR(50) DEFAULT 'active',
    "employee_number_enc" TEXT,
    "employee_number_idx" VARCHAR(64),
    "employee_number_key_version" SMALLINT NOT NULL DEFAULT 1,
    "company_id" INT NOT NULL REFERENCES "company" ("id") ON DELETE CASCADE,
    "local_id" INT REFERENCES "local" ("id") ON DELETE CASCADE,
    "org_unit_id" INT REFERENCES "org_units" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_user_compan_user_id_06e336" UNIQUE ("user_id", "company_id")
);
CREATE INDEX IF NOT EXISTS "idx_user_compan_employe_1dee5d" ON "user_companies" ("employee_number_idx");
CREATE TABLE IF NOT EXISTS "user_identities" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "identity_type" VARCHAR(50) NOT NULL,
    "is_primary" BOOL NOT NULL DEFAULT False,
    "is_verified" BOOL NOT NULL DEFAULT False,
    "verified_at" TIMESTAMPTZ,
    "identifier_enc" TEXT,
    "identifier_idx" VARCHAR(64) UNIQUE,
    "identifier_key_version" SMALLINT NOT NULL DEFAULT 1,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS "idx_user_identi_identif_ae30b2" ON "user_identities" ("identifier_idx");
CREATE TABLE IF NOT EXISTS "login_attempts" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "identity_type" VARCHAR(50),
    "identifier_used" VARCHAR(255),
    "auth_method" VARCHAR(50),
    "outcome" VARCHAR(50) NOT NULL,
    "ip_address" VARCHAR(45),
    "user_agent" VARCHAR(512),
    "attempted_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "application_id" INT REFERENCES "applications" ("id") ON DELETE CASCADE,
    "user_id" INT REFERENCES "users" ("id") ON DELETE CASCADE,
    "user_identity_id" INT REFERENCES "user_identities" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "userlog" (
    "id" BIGSERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "action" VARCHAR(50) NOT NULL,
    "table_affected" VARCHAR(50) NOT NULL,
    "old_values" JSONB,
    "new_values" JSONB,
    "timestamp" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "changed_by_id" INT REFERENCES "users" ("id") ON DELETE CASCADE,
    "user_target_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(100) NOT NULL,
    "content" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "role_app_windows" (
    "role_id" INT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE,
    "appwindow_id" INT NOT NULL REFERENCES "app_windows" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_role_app_wi_role_id_d5e0c7" ON "role_app_windows" ("role_id", "appwindow_id");
CREATE TABLE IF NOT EXISTS "role_permission" (
    "role_id" INT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE,
    "permission_id" INT NOT NULL REFERENCES "permission" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_role_permis_role_id_7454bb" ON "role_permission" ("role_id", "permission_id");
CREATE TABLE IF NOT EXISTS "role_users" (
    "role_id" INT NOT NULL REFERENCES "role" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE UNIQUE INDEX IF NOT EXISTS "uidx_role_users_role_id_c8adfc" ON "role_users" ("role_id", "user_id");"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """


MODELS_STATE = (
    "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"
)
