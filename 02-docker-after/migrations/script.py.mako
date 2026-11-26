"""${message}"""

from migrations.sqlfile import run_sql_file

revision: str = ${repr(up_revision)}
down_revision: str | None = ${repr(down_revision)}
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    run_sql_file("V?__?.sql")


def downgrade() -> None:
    raise NotImplementedError
