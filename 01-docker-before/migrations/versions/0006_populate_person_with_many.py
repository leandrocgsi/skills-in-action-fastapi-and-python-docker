"""Populate Person With Many"""

from migrations.sqlfile import run_sql_file

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V6__Populate_Person_With_Many.sql")


def downgrade() -> None:
    raise NotImplementedError
