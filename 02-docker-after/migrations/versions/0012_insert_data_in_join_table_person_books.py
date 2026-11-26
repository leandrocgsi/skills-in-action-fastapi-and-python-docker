"""Insert Data In Join Table Person Books"""

from migrations.sqlfile import run_sql_file

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V12__Insert_Data_In_Join_Table_Person_Books.sql")


def downgrade() -> None:
    raise NotImplementedError
