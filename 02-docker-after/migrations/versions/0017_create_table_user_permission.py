"""Create Table User Permission"""

from migrations.sqlfile import run_sql_file

revision: str = "0017"
down_revision: str | None = "0016"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V17__Create_Table_User_Permission.sql")


def downgrade() -> None:
    raise NotImplementedError
