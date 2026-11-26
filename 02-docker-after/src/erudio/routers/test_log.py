import logging

from fastapi import APIRouter, Depends, Response
from fastapi.responses import PlainTextResponse

from erudio.core.auth import current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/test/v1", tags=["Test Log"], dependencies=[Depends(current_user)])


@router.get(
    "", name="test_log", summary="Generates one log per level", response_class=PlainTextResponse
)
async def test_log() -> Response:
    logger.debug("This is an DEBUG log")
    logger.info("This is an INFO log")
    logger.warning("This is an WARN log")
    logger.error("This is an ERROR log")
    return PlainTextResponse("Logs generated successfully!")
