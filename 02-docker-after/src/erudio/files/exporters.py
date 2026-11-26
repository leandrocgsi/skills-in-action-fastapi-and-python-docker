import csv
import io
from collections.abc import Callable, Sequence

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

from erudio.schemas.person import PersonResponse

CSV = "text/csv"
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
HEADERS = ("ID", "First Name", "Last Name", "Address", "Gender", "Enabled")


def export_csv(people: Sequence[PersonResponse]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(HEADERS)
    for person in people:
        writer.writerow(
            [
                person.id,
                person.first_name,
                person.last_name,
                person.address,
                person.gender,
                str(person.enabled).lower(),
            ]
        )
    return buffer.getvalue().encode()


def export_xlsx(people: Sequence[PersonResponse]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    if sheet is None:
        raise RuntimeError
    sheet.title = "People"
    sheet.append(HEADERS)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
    for person in people:
        sheet.append(
            [
                person.id,
                person.first_name,
                person.last_name,
                person.address,
                person.gender,
                "Yes" if person.enabled else "No",
            ]
        )
    for index, column in enumerate(sheet.columns, start=1):
        width = max(len(str(cell.value)) for cell in column if cell.value is not None)
        sheet.column_dimensions[get_column_letter(index)].width = width + 2
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


EXPORTERS: dict[str, tuple[str, Callable[[Sequence[PersonResponse]], bytes]]] = {
    CSV: (".csv", export_csv),
    XLSX: (".xlsx", export_xlsx),
}
