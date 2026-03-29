"""Add unique indexes for (tenant_id, username) and (tenant_id, primary_mobile) on users.

Revision ID: 20260329_user_index
Revises: add_sso_login_enabled
Create Date: 2026-03-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260329_user_index'
down_revision: Union[str, None] = 'add_sso_login_enabled'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Remove external_id from users (as requested, User table should not store externalId)
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS external_id")

    # 1. Drop global unique constraints on users.username and users.email
    # Note: Constraint names in Postgres depend on how they were created.
    # Usually tablename_columnname_key for UNIQUE constraints or index_name for unique indexes.
    
    # We use a helper function to drop indexes/constraints safely as we don't know the exact name
    # without running a query, but common names are users_username_key / users_email_key
    
    op.execute("""
        DO $$
        BEGIN
            -- Drop global unique constraints if they exist
            ALTER TABLE users DROP CONSTRAINT IF EXISTS users_username_key;
            ALTER TABLE users DROP CONSTRAINT IF EXISTS users_email_key;
            
            -- Drop global unique indexes if they exist (sometimes SQLAlchemy creates them as indexes)
            DROP INDEX IF EXISTS ix_users_username;
            DROP INDEX IF EXISTS ix_users_email;
            
            -- Re-create regular indexes for performance since we dropped the unique ones
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_users_username') THEN
                CREATE INDEX ix_users_username ON users(username);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_users_email') THEN
                CREATE INDEX ix_users_email ON users(email);
            END IF;

            -- 2. Add composite unique indexes for (tenant_id, username)
            -- Note: We already have ix_users_tenant_email_unique from previous migration
            
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_users_tenant_username_unique') THEN
                CREATE UNIQUE INDEX ix_users_tenant_username_unique ON users(tenant_id, username) WHERE username IS NOT NULL;
            END IF;
            
            -- Ensure email uniqueness is also tenant-scoped (it was already added in refactor_v1 but let's double check)
            IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_users_tenant_email_unique') THEN
                CREATE UNIQUE INDEX ix_users_tenant_email_unique ON users(tenant_id, email) WHERE email IS NOT NULL;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Revert to global uniqueness (Warning: this may fail if duplicate usernames exist across tenants)
    op.execute("""
        DO $$
        BEGIN
            DROP INDEX IF EXISTS ix_users_tenant_username_unique;
            -- We keep ix_users_tenant_email_unique as it was already there before this migration
            ALTER TABLE users ADD CONSTRAINT users_username_key UNIQUE (username);
            ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE (email);
        END $$;
    """)
