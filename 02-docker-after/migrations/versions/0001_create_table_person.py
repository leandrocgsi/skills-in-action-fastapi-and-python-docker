"""Create Table Person"""

from migrations.sqlfile import run_sql_file

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V1__Create_Table_Person.sql")


def downgrade() -> None:
    raise NotImplementedError
