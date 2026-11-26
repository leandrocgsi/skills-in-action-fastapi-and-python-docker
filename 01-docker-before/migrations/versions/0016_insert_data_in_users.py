"""Insert Data In Users"""

from migrations.sqlfile import run_sql_file

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V16__Insert_Data_In_Users.sql")


def downgrade() -> None:
    raise NotImplementedError
