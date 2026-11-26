"""Alter Table Person"""

from migrations.sqlfile import run_sql_file

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V5__Alter_Table_Person.sql")


def downgrade() -> None:
    raise NotImplementedError
