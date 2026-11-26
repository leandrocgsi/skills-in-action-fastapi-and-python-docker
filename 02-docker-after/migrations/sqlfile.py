from collections.abc import Iterator
from pathlib import Path

import sqlparse
from alembic import op
from sqlparse import lexer
from sqlparse import tokens as T

SQL_DIR = Path(__file__).parent / "sql"


def _is_blank(statement: str) -> bool:
    return all(
        kind in T.Whitespace or kind in T.Comment or (kind in T.Punctuation and value == ";")
        for kind, value in lexer.tokenize(statement)  # type: ignore[no-untyped-call]
    )


def statements(text: str) -> Iterator[str]:
    for raw in sqlparse.split(text):
        if not _is_blank(raw):
            yield raw.strip().rstrip(";")


def run_sql_file(name: str) -> None:
    text = (SQL_DIR / name).read_text(encoding="utf-8-sig")
    connection = op.get_bind()
    for statement in statements(text):
        connection.exec_driver_sql(statement)
