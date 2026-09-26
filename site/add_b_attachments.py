"""Record visually bounded Annex B advice and project-schedule documents.

The spans were checked against rendered page images and their printed page
numbers. A separate page-by-page visual review confirms the p142–154 packet
repeats the content of p128–140 (see audit/annex_b_duplicate_packet.md).
"""

from __future__ import annotations

import json
from pathlib import Path


DATA = Path(__file__).parent / "data"


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def write(name: str, payload):
    (DATA / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


document_data = read("documents.json")
documents = document_data["records"]
existing = {item["id"] for item in documents}
records = [
    ("B-p116-117", "Advice of SARO letter", 116, 117, "SARO-BMB-A-24-0016272", ["B-p114", "B-p118-126"], None),
    ("B-p118-126", "Annex A project schedule", 118, 126, "SARO-BMB-A-24-0016272", ["B-p114", "B-p116-117"], None),
    ("B-p128-129", "Advice of SAROs issued", 128, 129, None, ["B-p127", "B-p141", "B-p130-140"], None),
    ("B-p130-140", "Annex A project schedule", 130, 140, "SARO-BMB-A-24-0017624", ["B-p141", "B-p128-129"], None),
    ("B-p142-143", "Advice of SAROs issued", 142, 143, None, ["B-p127", "B-p141", "B-p144-154"], "B-p128-129"),
    ("B-p144-154", "Annex A project schedule", 144, 154, "SARO-BMB-A-24-0017624", ["B-p141", "B-p142-143"], "B-p130-140"),
]
for identifier, kind, first, last, saro, related, duplicate in records:
    if identifier in existing:
        continue
    item = {
        "id": identifier,
        "annexId": "B",
        "type": kind,
        "pageStart": first,
        "pageEnd": last,
        "title": kind,
        "source": f"../court-documents/Annex-B-Compliance-G.R.-No.271059.pdf#page={first}",
        "audit": f"audit/annex_b.md (PDF pp. {first}–{last})",
        "relatedIds": related,
    }
    if saro:
        item["saroNumber"] = saro
    if duplicate:
        item["duplicateOf"] = duplicate
    documents.append(item)
documents.sort(key=lambda item: (item["annexId"], item["pageStart"], item["pageEnd"]))
write("documents.json", document_data)

saro_data = read("saros.json")
relations = {
    "B-p114": ["B-p116-117", "B-p118-126"],
    "B-p127": ["B-p128-129", "B-p142-143"],
    "B-p141": ["B-p128-129", "B-p130-140", "B-p142-143", "B-p144-154"],
}
for item in saro_data["records"]:
    for related in relations.get(item.get("orderDocumentId"), []):
        if related not in item.setdefault("relatedDocumentIds", []):
            item["relatedDocumentIds"].append(related)
write("saros.json", saro_data)
print(f"Indexed {len(records)} visually bounded Annex B documents")
