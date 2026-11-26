import logging

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_generates_one_log_per_level(
    client: AsyncClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.DEBUG):
        response = await client.get("/api/test/v1")

    assert response.status_code == 200
    assert response.headers["content-type"].split(";")[0] == "text/plain"
    assert response.text == "Logs generated successfully!"
    logged = [
        (record.levelname, record.getMessage())
        for record in caplog.records
        if record.name.startswith("erudio.")
    ]
    assert logged == [
        ("DEBUG", "This is an DEBUG log"),
        ("INFO", "This is an INFO log"),
        ("WARNING", "This is an WARN log"),
        ("ERROR", "This is an ERROR log"),
    ]


async def test_it_needs_a_token(anonymous: AsyncClient) -> None:
    assert (await anonymous.get("/api/test/v1")).status_code == 401
