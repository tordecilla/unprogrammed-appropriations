"""Export visually cited UA status-report pages as small source PDFs.

Page references are supplied by visual transcriptions in status_rows.json and
status_allocations.json. This script only splits those known pages; it does not
read or classify PDF contents.
"""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


SITE = Path(__file__).parent
DATA = SITE / "data"
OUTPUT = SITE / "status-pages"
SOURCES = SITE.parent / "court-documents"


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def write(name: str, payload):
    (DATA / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


annexes = {row["id"].removeprefix("annex-").upper(): row for row in read("annexes.json")["records"]}
rows = read("status_rows.json")
allocations = read("status_allocations.json")
rollups = read("status_rollups.json")
notes = read("status_report_notes.json")
pages = {(row["sourceAnnex"], page) for row in rows["records"] for page in row["sourcePages"]}
pages.update((cell["sourceAnnex"], cell["sourcePage"]) for cell in allocations["records"])
pages.update((cell["sourceAnnex"], cell["sourcePage"]) for cell in rollups["records"])
pages.update((note["sourceAnnex"], note["sourcePage"]) for note in notes["records"])
OUTPUT.mkdir(exist_ok=True)
readers = {}
for code, page in sorted(pages):
    if code not in readers:
        readers[code] = PdfReader(str(SOURCES / annexes[code]["file"]))
    reader = readers[code]
    if not 1 <= page <= len(reader.pages):
        raise ValueError(f"Annex {code} page {page} is outside the PDF")
    filename = f"annex-{code.lower()}-p{page:03d}.pdf"
    writer = PdfWriter()
    writer.add_page(reader.pages[page - 1])
    writer.add_metadata({"/Title": f"Annex {code} page {page}", "/Subject": "UA status report source page"})
    with (OUTPUT / filename).open("wb") as stream:
        writer.write(stream)

for row in rows["records"]:
    row["sourcePagePdfs"] = [f"status-pages/annex-{row['sourceAnnex'].lower()}-p{page:03d}.pdf" for page in row["sourcePages"]]
for cell in allocations["records"]:
    cell["standalonePdf"] = f"status-pages/annex-{cell['sourceAnnex'].lower()}-p{cell['sourcePage']:03d}.pdf"
write("status_rows.json", rows)
write("status_allocations.json", allocations)
print(f"Exported {len(pages)} one-page status PDFs")
