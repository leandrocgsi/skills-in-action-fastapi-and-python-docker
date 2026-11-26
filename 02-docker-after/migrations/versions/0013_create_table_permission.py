"""Create Table Permission"""

from migrations.sqlfile import run_sql_file

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V13__Create_Table_Permission.sql")


def downgrade() -> None:
    raise NotImplementedError
