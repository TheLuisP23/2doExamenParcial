"""create books (REQ-A-012)

Revision ID: 0001
"""

from __future__ import annotations

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
    op.execute(
        "CREATE OR REPLACE FUNCTION immutable_unaccent(text) RETURNS text "
        "AS $$ SELECT public.unaccent('public.unaccent', $1) $$ LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT"
    )
    op.execute(
        """
        CREATE TABLE books (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          isbn varchar(13) NOT NULL CONSTRAINT uq_books_isbn UNIQUE CHECK (isbn ~ '^97[89][0-9]{10}$'),
          title varchar(255) NOT NULL CHECK (length(btrim(title)) > 0),
          author varchar(255) NOT NULL CHECK (length(btrim(author)) > 0),
          publisher varchar(255),
          published_year smallint CHECK (published_year BETWEEN 1450 AND 2100),
          genre varchar(64),
          created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX ix_books_created_at_id ON books (created_at DESC, id)")
    op.execute(
        "CREATE INDEX ix_books_title_trgm ON books USING gin (immutable_unaccent(lower(title)) gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX ix_books_author_trgm ON books USING gin (immutable_unaccent(lower(author)) gin_trgm_ops)"
    )
    op.execute("CREATE INDEX ix_books_genre_lower ON books (lower(genre))")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS books")
    op.execute("DROP FUNCTION IF EXISTS immutable_unaccent(text)")
