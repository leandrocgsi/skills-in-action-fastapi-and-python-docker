from typing import Annotated

from fastapi import Depends, Request

from erudio.core.config import Settings


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


def issuer_of(request: Request) -> str:
    return str(request.base_url).rstrip("/")
