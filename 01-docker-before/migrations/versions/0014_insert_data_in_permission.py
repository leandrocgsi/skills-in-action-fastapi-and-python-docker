"""Insert Data In Permission"""

from migrations.sqlfile import run_sql_file

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V14__Insert_Data_In_Permission.sql")


def downgrade() -> None:
    raise NotImplementedError
