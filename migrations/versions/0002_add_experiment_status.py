"""Añade el estado de los experimentos conservando los registros existentes."""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "experiments",
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'completed'"),
        ),
    )


def downgrade():
    op.drop_column("experiments", "status")
