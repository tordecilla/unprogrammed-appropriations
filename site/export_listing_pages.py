"""Split visually transcribed eBudget source pages into one-page PDFs.

The page numbers come only from manually staged transaction rows. PDF parsing
here is used for export, not text extraction or record classification.
"""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


SITE = Path(__file__).parent
DATA = SITE / "data"
OUTPUT = SITE / "listing-pages"
SOURCES = SITE.parent / "court-documents"


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


annexes = {row["id"].removeprefix("annex-").upper(): row for row in read("annexes.json")["records"]}
rows = read("ebudget_transactions.json")["records"]
pages = sorted({(row["sourceAnnex"], row["sourcePage"]) for row in rows})
OUTPUT.mkdir(exist_ok=True)
readers = {}
for code, page in pages:
    if code not in readers:
        readers[code] = PdfReader(str(SOURCES / annexes[code]["file"]))
    reader = readers[code]
    if not 1 <= page <= len(reader.pages):
        raise ValueError(f"Annex {code} page {page} is outside the PDF")
    writer = PdfWriter()
    writer.add_page(reader.pages[page - 1])
    writer.add_metadata({"/Title": f"Annex {code} page {page}", "/Subject": "eBudget listing source page"})
    with (OUTPUT / f"annex-{code.lower()}-p{page:03d}.pdf").open("wb") as stream:
        writer.write(stream)

print(f"Exported {len(pages)} one-page eBudget listing PDFs")
