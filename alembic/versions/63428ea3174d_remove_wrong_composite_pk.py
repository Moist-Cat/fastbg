"""Remove wrong composite pk

Revision ID: 63428ea3174d
Revises: 138836a7e4b2
Create Date: 2025-11-02 11:56:02.168747

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "63428ea3174d"
down_revision: Union[str, Sequence[str], None] = "138836a7e4b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "post_tags_new",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("post_id", sa.Integer(), sa.ForeignKey("post.id"), nullable=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tag.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.execute(
        "INSERT INTO post_tags_new (post_id, tag_id, created_at, updated_at) SELECT post_id, tag_id, created_at, updated_at FROM post_tags"
    )

    op.drop_table("post_tags")

    op.rename_table("post_tags_new", "post_tags")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "post_tags_old",
        sa.Column(
            "post_id",
            sa.Integer(),
            sa.ForeignKey("post.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "tag_id",
            sa.Integer(),
            sa.ForeignKey("tag.id"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.execute(
        "INSERT INTO post_tags_old (post_id, tag_id, created_at, updated_at) SELECT post_id, tag_id, created_at, updated_at FROM post_tags"
    )

    op.drop_table("post_tags")

    op.rename_table("post_tags_old", "post_tags")
