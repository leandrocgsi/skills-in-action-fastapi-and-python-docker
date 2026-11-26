"""Convert Books to utf8mb4 (port-only; the Java V3 and V11 scripts create them as latin1)"""

from alembic import op

revision: str = "0019"
down_revision: str | None = "0018"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE books CONVERT TO CHARACTER SET utf8mb4")
    op.execute("ALTER TABLE person_books CONVERT TO CHARACTER SET utf8mb4")


def downgrade() -> None:
    raise NotImplementedError
