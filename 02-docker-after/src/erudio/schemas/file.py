from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class UploadFileResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    file_name: str
    file_download_uri: str
    file_type: str | None
    size: int
