"""Insert Data In User Permission"""

from migrations.sqlfile import run_sql_file

revision: str = "0018"
down_revision: str | None = "0017"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V18__Insert_Data_In_User_Permission.sql")


def downgrade() -> None:
    raise NotImplementedError
