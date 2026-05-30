"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("adzuna_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("company", sa.Text()),
        sa.Column("location", sa.Text()),
        sa.Column("category", sa.Text()),
        sa.Column("seniority", sa.Text()),
        sa.Column("required_skills", sa.ARRAY(sa.Text())),
        sa.Column("nice_to_have", sa.ARRAY(sa.Text())),
        sa.Column("soft_skills", sa.ARRAY(sa.Text())),
        sa.Column("languages", sa.ARRAY(sa.Text())),
        sa.Column("redirect_url", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(3072)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "fetched_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True)),
        sa.UniqueConstraint("adzuna_id"),
    )

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "user_profiles",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("cv_text", sa.Text()),
        sa.Column("skills", sa.ARRAY(sa.Text())),
        sa.Column("seniority", sa.Text()),
        sa.Column("languages", sa.ARRAY(sa.Text())),
        sa.Column("embedding", Vector(3072)),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "match_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("jobs.id"),
            nullable=False,
        ),
        sa.Column("score", sa.Float()),
        sa.Column(
            "matched_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
        ),
        sa.Column("applied", sa.Boolean(), server_default=sa.text("false")),
    )



def downgrade() -> None:
    op.drop_table("match_history")
    op.drop_table("user_profiles")
    op.drop_table("users")
    op.drop_table("jobs")
    op.execute("DROP EXTENSION IF EXISTS vector")
