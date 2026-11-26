from collections.abc import Sequence
from enum import StrEnum


class MediaType(StrEnum):
    JSON = "application/json"
    XML = "application/xml"
    YAML = "application/yaml"


OFFERED: tuple[MediaType, ...] = (MediaType.JSON, MediaType.XML, MediaType.YAML)

_YAML_ALIASES = {"application/yaml", "application/x-yaml", "text/yaml"}


def bare(content_type: str | None) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def request_media_type(content_type: str | None) -> MediaType | None:
    value = bare(content_type)
    if value == MediaType.JSON or value.endswith("+json"):
        return MediaType.JSON
    if value == MediaType.XML:
        return MediaType.XML
    if value in _YAML_ALIASES:
        return MediaType.YAML
    return None


def _parse_ranges(header: str) -> list[tuple[str, float, int, int]]:
    ranges: list[tuple[str, float, int, int]] = []
    for position, part in enumerate(header.split(",")):
        pieces = [piece.strip() for piece in part.split(";")]
        media_range = pieces[0].lower()
        if "/" not in media_range:
            continue
        quality = 1.0
        for parameter in pieces[1:]:
            name, _, value = parameter.partition("=")
            if name.strip().lower() == "q":
                try:
                    quality = float(value)
                except ValueError:
                    quality = 0.0
        specificity = 0 if media_range == "*/*" else 1 if media_range.endswith("/*") else 2
        ranges.append((media_range, quality, specificity, position))
    return sorted(ranges, key=lambda item: (-item[1], -item[2], item[3]))


def _matches(media_range: str, candidate: str) -> bool:
    if media_range == "*/*":
        return True
    if media_range.endswith("/*"):
        return candidate.startswith(media_range[:-1])
    return media_range == candidate


def select_offered(accept: str | None, offered: Sequence[str]) -> str | None:
    if accept is None or not accept.strip():
        return offered[0]
    ranges = _parse_ranges(accept)
    refused = {media_range for media_range, quality, _, _ in ranges if quality <= 0}
    for media_range, quality, _, _ in ranges:
        if quality <= 0:
            continue
        for candidate in offered:
            if _matches(media_range, candidate) and candidate not in refused:
                return candidate
    return None


def select_media_type(
    accept: str | None, offered: Sequence[MediaType] = OFFERED
) -> MediaType | None:
    chosen = select_offered(accept, [media.value for media in offered])
    return MediaType(chosen) if chosen is not None else None
