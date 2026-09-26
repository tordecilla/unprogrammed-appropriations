"""Export visually bounded source records as standalone PDFs.

The page ranges come from visual review in documents.json. This script does not
read PDF text or infer document boundaries.
"""

from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter


SITE = Path(__file__).parent
DATA = SITE / "data"
OUTPUT = SITE / "documents"
SOURCES = SITE.parent / "court-documents"


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


sources = {
    row["id"].removeprefix("annex-").upper(): row
    for row in read("annexes.json")["records"]
}
catalog = read("documents.json")
OUTPUT.mkdir(exist_ok=True)
readers: dict[str, PdfReader] = {}

for document in catalog["records"]:
    code = document["annexId"]
    if code not in readers:
        readers[code] = PdfReader(str(SOURCES / sources[code]["file"]))
    reader = readers[code]
    first = document["pageStart"]
    last = document["pageEnd"]
    if not 1 <= first <= last <= len(reader.pages):
        raise ValueError(f"Invalid page range for {document['id']}: {first}-{last}")
    filename = f"{document['id']}.pdf"
    writer = PdfWriter()
    for page_index in range(first - 1, last):
        writer.add_page(reader.pages[page_index])
    writer.add_metadata({
        "/Title": document.get("saroNumber") or document.get("title") or document["id"],
        "/Subject": f"Annex {code}, original PDF pages {first}-{last}",
    })
    with (OUTPUT / filename).open("wb") as stream:
        writer.write(stream)
    exported = PdfReader(str(OUTPUT / filename))
    if len(exported.pages) != last - first + 1:
        raise ValueError(f"Export page count mismatch for {document['id']}")
    document["standalonePdf"] = f"documents/{filename}"

(DATA / "documents.json").write_text(
    json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"Exported {len(catalog['records'])} standalone documents to {OUTPUT}")
