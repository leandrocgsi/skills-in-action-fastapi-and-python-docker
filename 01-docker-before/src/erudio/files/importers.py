import csv
import io
from collections.abc import Callable

from openpyxl import load_workbook

from erudio.schemas.person import PersonCreate

COLUMNS = ("first_name", "last_name", "address", "gender")


class FileProcessingError(Exception):
    pass


def _person(values: list[str]) -> PersonCreate:
    first_name, last_name, address, gender = values
    return PersonCreate(
        first_name=first_name, last_name=last_name, address=address, gender=gender, enabled=True
    )


def import_csv(data: bytes) -> list[PersonCreate]:
    try:
        text = data.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text), skipinitialspace=True)
        header = {name.strip() for name in reader.fieldnames or []}
        if not set(COLUMNS) <= header:
            raise FileProcessingError
        people: list[PersonCreate] = []
        for record in reader:
            cleaned = {(key or "").strip(): value for key, value in record.items()}
            values = [cleaned.get(column) for column in COLUMNS]
            if all(value is None or not value.strip() for value in values):
                continue
            if any(value is None for value in values):
                raise FileProcessingError
            people.append(_person([str(value).strip() for value in values]))
    except FileProcessingError:
        raise
    except (UnicodeDecodeError, csv.Error, ValueError) as error:
        raise FileProcessingError from error
    return people


def import_xlsx(data: bytes) -> list[PersonCreate]:
    try:
        workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
        rows = workbook.worksheets[0].iter_rows(values_only=True)
        next(rows, None)
        people: list[PersonCreate] = []
        for row in rows:
            if not row or row[0] is None or not str(row[0]).strip():
                continue
            values = list(row[: len(COLUMNS)])
            if len(values) < len(COLUMNS) or any(value is None for value in values):
                raise FileProcessingError
            people.append(_person([str(value).strip() for value in values]))
        workbook.close()
    except FileProcessingError:
        raise
    except Exception as error:
        raise FileProcessingError from error
    return people


IMPORTERS: dict[str, Callable[[bytes], list[PersonCreate]]] = {
    ".csv": import_csv,
    ".xlsx": import_xlsx,
}
