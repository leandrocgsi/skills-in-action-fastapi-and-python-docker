"""Alter Table Person Adding Photo And Wiki"""

from migrations.sqlfile import run_sql_file

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V8__Alter_Table_Person_Adding_Photo_And_Wiki.sql")


def downgrade() -> None:
    raise NotImplementedError
