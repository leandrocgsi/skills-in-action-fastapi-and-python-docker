"""Create Table Users"""

from migrations.sqlfile import run_sql_file

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V15__Create_Table_Users.sql")


def downgrade() -> None:
    raise NotImplementedError
