"""Export visually identified advice evidence pages cited by signed SARO lines.

The source pages and relationships come from visual transcriptions. PDF access
here only splits those known pages for direct citation.
"""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


SITE = Path(__file__).parent
DATA = SITE / "data"
annexes = {row["id"]: row for row in json.loads((DATA / "annexes.json").read_text(encoding="utf-8"))["records"]}
lines = json.loads((DATA / "particulars.json").read_text(encoding="utf-8"))["records"]
advice_items = json.loads((DATA / "advice_items.json").read_text(encoding="utf-8"))["records"]
documents = json.loads((DATA / "documents.json").read_text(encoding="utf-8"))["records"]
pages = sorted(
    {("B", row["adviceSourcePage"], row["adviceSourcePdf"]) for row in lines if row.get("adviceSourcePdf")}
    | {(row["sourceAnnex"], row["sourcePage"], row["sourcePdf"]) for row in advice_items}
    | {(document["annexId"], evidence["sourcePage"], evidence["sourcePdf"]) for document in documents for evidence in document.get("statusEvidence", [])}
)
readers = {}
for code, page, output_path in pages:
    if code not in readers:
        readers[code] = PdfReader(str(SITE.parent / "court-documents" / annexes[f"annex-{code.lower()}"]["file"]))
    reader = readers[code]
    if not 1 <= page <= len(reader.pages):
        raise ValueError(f"Annex {code} page {page} is outside the PDF")
    output = SITE / output_path
    output.parent.mkdir(exist_ok=True)
    writer = PdfWriter()
    writer.add_page(reader.pages[page - 1])
    writer.add_metadata({"/Title": f"Annex {code} advice page {page}", "/Subject": "SARO supporting advice evidence"})
    with output.open("wb") as stream:
        writer.write(stream)
print(f"Exported {len(pages)} one-page advice evidence PDFs")
