"""Inserting Wikipedia Url"""

from migrations.sqlfile import run_sql_file

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V9__Inserting_Wikipedia_Url.sql")


def downgrade() -> None:
    raise NotImplementedError
