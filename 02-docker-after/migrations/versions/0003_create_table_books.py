"""Create Table Books"""

from migrations.sqlfile import run_sql_file

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V3__Create_Table_Books.sql")


def downgrade() -> None:
    raise NotImplementedError
