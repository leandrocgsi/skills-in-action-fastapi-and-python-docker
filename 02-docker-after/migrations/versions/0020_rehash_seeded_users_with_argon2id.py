"""Rehash the seeded users with Argon2id (port-only; the Java V16 script seeds Spring's PBKDF2)"""

from alembic import op
from sqlalchemy import text

revision: str = "0020"
down_revision: str | None = "0019"
branch_labels: str | None = None
depends_on: str | None = None

ARGON2ID = "$argon2id$v=19$m=65536,t=3,p=4$"

# user_name, PBKDF2 hash seeded by V16, Argon2id hash of the same password (leandro: admin123,
# flavio: admin234).
SEEDED_USERS = (
    (
        "leandro",
        "1e3cdeeaaaeeda173ff6d002e7cb5e3f91ebc354dcff52156c9eaba1793a3a5e5bee306c11099e22",
        ARGON2ID + "oMW5+s5nhG9AjFtTvva1Ig$NaWRy1R/rpDLqOd/LF7Y0v7fx/l0umVOLy2As2RrCzE",
    ),
    (
        "flavio",
        "362ad02420268beeb22d3a1f0d92749df461d7f4b74c9433d7415bdeef1b2902f4eb1edaecb37cb3",
        ARGON2ID + "nIHHJEPXChPvKTcuhHgW0Q$/e3EV8yJaLbzjSPEpQ8EeiYWGfi1eSE2QDRWo+9zmx8",
    ),
)


def upgrade() -> None:
    update = text("UPDATE users SET password = :argon2 WHERE user_name = :name AND password = :old")
    for name, old, argon2 in SEEDED_USERS:
        op.get_bind().execute(update, {"name": name, "old": old, "argon2": argon2})


def downgrade() -> None:
    raise NotImplementedError
