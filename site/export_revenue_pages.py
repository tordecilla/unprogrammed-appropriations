"""Split visually identified Annex J pages for direct source links."""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


SITE = Path(__file__).parent
DATA = SITE / "data"
OUTPUT = SITE / "revenue-pages"
annex = next(row for row in json.loads((DATA / "annexes.json").read_text(encoding="utf-8"))["records"] if row["id"] == "annex-j")
documents = json.loads((DATA / "revenue_evidence.json").read_text(encoding="utf-8"))["records"]
reader = PdfReader(str(SITE.parent / "court-documents" / annex["file"]))
OUTPUT.mkdir(exist_ok=True)
pages = sorted({row["sourcePage"] for row in documents} | {1, 2, 3, 25})
for page in pages:
    if not 1 <= page <= len(reader.pages):
        raise ValueError(f"Annex J page {page} outside PDF")
    writer = PdfWriter()
    writer.add_page(reader.pages[page - 1])
    writer.add_metadata({"/Title": f"Annex J page {page}", "/Subject": "Revenue status or evidence source page"})
    with (OUTPUT / f"annex-j-p{page:03d}.pdf").open("wb") as stream:
        writer.write(stream)
print(f"Exported {len(pages)} one-page Annex J source PDFs")
