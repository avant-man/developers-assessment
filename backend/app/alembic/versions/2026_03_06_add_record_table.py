"""Add record table for settlement domain

Revision ID: a1b2c3d4e5f6
Revises: 1a31ce608336
Create Date: 2026-03-06

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


revision = "a1b2c3d4e5f6"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "record",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "type", sqlmodel.sql.sqltypes.AutoString(length=64), nullable=False
        ),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("data", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["parent_id"], ["record.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
    )
    op.create_index(op.f("ix_record_type"), "record", ["type"], unique=False)
    op.create_index(op.f("ix_record_parent_id"), "record", ["parent_id"], unique=False)
    op.create_index(op.f("ix_record_user_id"), "record", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_record_created_at"), "record", ["created_at"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_record_created_at"), table_name="record")
    op.drop_index(op.f("ix_record_user_id"), table_name="record")
    op.drop_index(op.f("ix_record_parent_id"), table_name="record")
    op.drop_index(op.f("ix_record_type"), table_name="record")
    op.drop_table("record")
