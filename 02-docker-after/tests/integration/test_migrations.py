import pytest
from fastapi import FastAPI
from sqlalchemy import text

pytestmark = pytest.mark.integration

COUNTS = {
    "person": "select count(*) from person",
    "books": "select count(*) from books",
    "permission": "select count(*) from permission",
    "users": "select count(*) from users",
    "user_permission": "select count(*) from user_permission",
    "person_books": "select count(*) from person_books",
}


async def test_seed_data_after_upgrade_head(app: FastAPI) -> None:
    async with app.state.engine.connect() as connection:
        counts = {
            table: (await connection.execute(text(query))).scalar_one()
            for table, query in COUNTS.items()
        }
        version = (
            await connection.execute(text("select version_num from alembic_version"))
        ).scalar_one()

    people = 9 + 200
    assert counts == {
        "person": people,
        "books": 215,
        "permission": 3,
        "users": 2,
        "user_permission": 3,
        "person_books": 9 * 20 + 200 * 3,
    }
    assert version == "0020"


async def test_seeded_users_and_roles(app: FastAPI) -> None:
    query = text(
        "select u.user_name, group_concat(p.description order by p.id) "
        "from users u join user_permission up on up.id_user = u.id "
        "join permission p on p.id = up.id_permission group by u.user_name order by u.user_name"
    )
    async with app.state.engine.connect() as connection:
        rows = (await connection.execute(query)).all()

    assert [tuple(row) for row in rows] == [("flavio", "ADMIN"), ("leandro", "ADMIN,MANAGER")]
