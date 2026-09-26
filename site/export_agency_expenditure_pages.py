"""Split cited Annex M pages into one-page PDFs; page numbers come from visual staging."""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


SITE = Path(__file__).parent
data = json.loads((SITE / "data" / "agency_expenditure.json").read_text(encoding="utf-8"))
annex = next(row for row in json.loads((SITE / "data" / "annexes.json").read_text(encoding="utf-8"))["records"] if row["id"] == "annex-m")
reader = PdfReader(str(SITE.parent / "court-documents" / annex["file"]))
output = SITE / "agency-expenditure-pages"
output.mkdir(exist_ok=True)
for page in data["transcribedPdfPages"]:
    if not 1 <= page <= len(reader.pages):
        raise ValueError(f"Annex M PDF page {page} outside source")
    writer = PdfWriter()
    writer.add_page(reader.pages[page - 1])
    writer.add_metadata({"/Title": f"Annex M page {page}", "/Subject": "Agency expenditure table source page"})
    with (output / f"annex-m-p{page:03d}.pdf").open("wb") as stream:
        writer.write(stream)
print(f"Exported {len(data['transcribedPdfPages'])} one-page Annex M PDFs")
