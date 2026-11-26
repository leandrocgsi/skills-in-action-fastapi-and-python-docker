"""Populate Books With Many"""

from migrations.sqlfile import run_sql_file

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V7__Populate_Books_With_Many.sql")


def downgrade() -> None:
    raise NotImplementedError
