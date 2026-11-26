"""Create Join Table Person Books"""

from migrations.sqlfile import run_sql_file

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V11__Create_Join_Table_Person_Books.sql")


def downgrade() -> None:
    raise NotImplementedError
