"""spec alignment: solution votes, merged contributions, temporary freeze

Revision ID: b7e21c9a4f10
Revises: 6d05700d8643
Create Date: 2026-11-14 09:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7e21c9a4f10"
down_revision: str | None = "6d05700d8643"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("reputation_frozen_until", sa.DateTime(timezone=True), nullable=True))
    op.add_column("contribution_requests", sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "solution_votes",
        sa.Column("solution_id", sa.Uuid(), nullable=False),
        sa.Column("voter_id", sa.Uuid(), nullable=False),
        sa.Column("is_demo", sa.Boolean(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["solution_id"], ["solutions.id"], name=op.f("fk_solution_votes_solution_id_solutions"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["voter_id"], ["users.id"], name=op.f("fk_solution_votes_voter_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_solution_votes")),
        sa.UniqueConstraint("solution_id", "voter_id", name="uq_solution_votes_solution_voter"),
    )
    op.create_index(op.f("ix_solution_votes_solution_id"), "solution_votes", ["solution_id"])
    op.create_index(op.f("ix_solution_votes_voter_id"), "solution_votes", ["voter_id"])

    # Roles were renamed: "entreprise" replaces the old sponsor label.
    op.execute("UPDATE user_roles SET role = 'company' WHERE role = 'sponsor'")


def downgrade() -> None:
    op.execute("UPDATE user_roles SET role = 'sponsor' WHERE role = 'company'")
    op.drop_index(op.f("ix_solution_votes_voter_id"), table_name="solution_votes")
    op.drop_index(op.f("ix_solution_votes_solution_id"), table_name="solution_votes")
    op.drop_table("solution_votes")
    op.drop_column("contribution_requests", "merged_at")
    op.drop_column("users", "reputation_frozen_until")
