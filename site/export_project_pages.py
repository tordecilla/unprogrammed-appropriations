"""Split visually cited attachment pages into small, one-page source PDFs."""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


SITE = Path(__file__).parent
DATA = SITE / "data"
OUTPUT = SITE / "project-pages"
SOURCES = SITE.parent / "court-documents"


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


annexes = {row["id"].removeprefix("annex-").upper(): row for row in read("annexes.json")["records"]}
items = read("project_items.json")["records"]
pages = sorted({(item["sourceAnnex"], item["sourcePage"]) for item in items})
readers = {}
OUTPUT.mkdir(exist_ok=True)
for code, page in pages:
    if code not in readers:
        readers[code] = PdfReader(str(SOURCES / annexes[code]["file"]))
    reader = readers[code]
    if not 1 <= page <= len(reader.pages):
        raise ValueError(f"Annex {code} page {page} is outside the PDF")
    writer = PdfWriter()
    writer.add_page(reader.pages[page - 1])
    writer.add_metadata({"/Title": f"Annex {code} page {page}", "/Subject": "Itemized project schedule source page"})
    filename = f"annex-{code.lower()}-p{page:03d}.pdf"
    with (OUTPUT / filename).open("wb") as stream:
        writer.write(stream)
print(f"Exported {len(pages)} one-page project PDFs")
