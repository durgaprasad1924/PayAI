"""add registration token

Revision ID: 96e83b9fabff
Revises: 23694c660d73
Create Date: 2026-09-22 16:31:30.015249

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96e83b9fabff'
down_revision: Union[str, Sequence[str], None] = '23694c660d73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "registration_challenges",
        sa.Column(
            "registration_token",
            sa.String(length=255),
            nullable=False
        )
    )

    op.create_unique_constraint(
        "uq_registration_challenges_registration_token",
        "registration_challenges",
        ["registration_token"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_registration_challenges_registration_token",
        "registration_challenges",
        type_="unique"
    )

    op.drop_column(
        "registration_challenges",
        "registration_token"
    )
