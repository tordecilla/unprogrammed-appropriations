"""Split visually indexed Annex N-P pages into one-page source PDFs."""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


SITE = Path(__file__).parent
annexes = {row["id"].removeprefix("annex-").upper(): row for row in json.loads((SITE / "data" / "annexes.json").read_text(encoding="utf-8"))["records"]}
rows = json.loads((SITE / "data" / "debt_reference.json").read_text(encoding="utf-8"))["records"]
pages = sorted({(row["sourceAnnex"], row["sourcePage"]) for row in rows})
readers = {}
output = SITE / "debt-pages"
output.mkdir(exist_ok=True)
for code, page in pages:
    if code not in readers:
        readers[code] = PdfReader(str(SITE.parent / "court-documents" / annexes[code]["file"]))
    reader = readers[code]
    if not 1 <= page <= len(reader.pages):
        raise ValueError(f"Annex {code} page {page} outside source")
    writer = PdfWriter()
    writer.add_page(reader.pages[page - 1])
    writer.add_metadata({"/Title": f"Annex {code} page {page}", "/Subject": "Debt reference source page"})
    with (output / f"annex-{code.lower()}-p{page:03d}.pdf").open("wb") as stream:
        writer.write(stream)
print(f"Exported {len(pages)} debt-reference one-page PDFs")
