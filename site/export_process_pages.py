"""Split visually indexed Annex K pages into one-page source PDFs."""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


SITE = Path(__file__).parent
annex = next(row for row in json.loads((SITE / "data" / "annexes.json").read_text(encoding="utf-8"))["records"] if row["id"] == "annex-k")
rows = json.loads((SITE / "data" / "process_steps.json").read_text(encoding="utf-8"))["records"]
reader = PdfReader(str(SITE.parent / "court-documents" / annex["file"]))
pages = sorted({row["sourcePage"] for row in rows})
output = SITE / "process-pages"
output.mkdir(exist_ok=True)
for page in pages:
    if not 1 <= page <= len(reader.pages):
        raise ValueError(f"Annex K page {page} outside source")
    writer = PdfWriter()
    writer.add_page(reader.pages[page - 1])
    writer.add_metadata({"/Title": f"Annex K page {page}", "/Subject": "UA release process source page"})
    with (output / f"annex-k-p{page:03d}.pdf").open("wb") as stream:
        writer.write(stream)
print(f"Exported {len(pages)} Annex K one-page PDFs")
