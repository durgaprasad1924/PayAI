"""add authentication fields to users

Revision ID: 69000eb396fc
Revises: 01eabe6bb951
Create Date: 2026-09-21 11:57:40.240716

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "69000eb396fc"
down_revision: Union[str, Sequence[str], None] = "01eabe6bb951"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "users",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )

    op.add_column(
        "users",
        sa.Column(
            "phone",
            sa.String(length=20),
            nullable=True
        )
    )

    op.add_column(
        "users",
        sa.Column(
            "phone_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false()
        )
    )

    op.create_unique_constraint(
        "uq_users_phone",
        "users",
        ["phone"]
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_constraint(
        "uq_users_phone",
        "users",
        type_="unique"
    )

    op.drop_column("users", "phone_verified")
    op.drop_column("users", "phone")
    op.drop_column("users", "email_verified")