"""Export cited Annex L pages after visual transcription established their bounds.

PDF access here only splits known pages into one-page source documents; it does
not extract or classify source content.
"""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


SITE = Path(__file__).parent
DATA = SITE / "data"
OUTPUT = SITE / "road-fund-pages"

annexes = json.loads((DATA / "annexes.json").read_text(encoding="utf-8"))["records"]
annex = next(row for row in annexes if row["id"] == "annex-l")
rows = json.loads((DATA / "road_fund_projects.json").read_text(encoding="utf-8"))["records"]
pages = sorted({row["sourcePage"] for row in rows})
summary = json.loads((DATA / "road_fund_summary.json").read_text(encoding="utf-8"))["records"]
pages = sorted(set(pages) | {row["sourcePage"] for row in summary})
reader = PdfReader(str(SITE.parent / "court-documents" / annex["file"]))
OUTPUT.mkdir(exist_ok=True)
for page in pages:
    if not 1 <= page <= len(reader.pages):
        raise ValueError(f"Annex L page {page} is outside the PDF")
    writer = PdfWriter()
    writer.add_page(reader.pages[page - 1])
    writer.add_metadata({"/Title": f"Annex L page {page}", "/Subject": "Special Road Fund project source page"})
    with (OUTPUT / f"annex-l-p{page:03d}.pdf").open("wb") as stream:
        writer.write(stream)

print(f"Exported {len(pages)} one-page Annex L PDFs")
