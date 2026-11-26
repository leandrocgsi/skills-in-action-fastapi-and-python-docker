"""Populate Table Person"""

from migrations.sqlfile import run_sql_file

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V2__Populate_Table_Person.sql")


def downgrade() -> None:
    raise NotImplementedError
