"""Index Annex B related documents bounded from rendered page images."""

from __future__ import annotations

import json
from pathlib import Path


DATA = Path(__file__).parent / "data"


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def write(name: str, payload):
    (DATA / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# id, type, start, end, signed SARO document, number, audit record
ATTACHMENTS = (
    ("B-p061", "Annex A project summary", 61, 61, "B-p059", "SARO-BMB-D-24-0015786", "audit/annex_b.md"),
    ("B-p63", "Annex A release schedule", 63, 63, "B-p062", "SARO-BMB-A-24-0000658", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p65", "Annex A release schedule", 65, 65, "B-p064", "SARO-BMB-A-24-0000659", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p67", "Annex A release schedule", 67, 67, "B-p066", "SARO-BMB-A-24-0000660", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p72", "Annex A release schedule", 72, 72, "B-p071", "SARO-BMB-A-24-0000656", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p74", "Annex A release schedule", 74, 74, "B-p073", "SARO-BMB-A-24-0000657", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p76", "Annex A release schedule", 76, 76, "B-p075", "SARO-BMB-A-24-0002833", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p78", "Annex A release schedule", 78, 78, "B-p077", "SARO-BMB-A-24-0002830", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p80", "Annex A release schedule", 80, 80, "B-p079", "SARO-BMB-A-24-0002832", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p82", "Annex A release schedule", 82, 82, "B-p081", "SARO-BMB-A-24-0002829", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p84", "Annex A release schedule", 84, 84, "B-p083", "SARO-BMB-A-24-0002831", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p93-94", "Annex A right-of-way schedule", 93, 94, "B-p090", "SARO-BMB-A-24-0004248", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p100-102", "Annex A release schedule", 100, 102, "B-p099", "SARO-BMB-A-24-0004247", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p111-113", "Annex A release schedule", 111, 113, "B-p108", "SARO-BMB-A-24-0014803", "audit/annex_b_62_117_schedule_audit.md"),
    ("B-p216", "Advice of SARO letter", 216, 216, "B-p215", "SARO-BMB-A-24-0018544", "audit/annex_b.md"),
    ("B-p217-223", "Annex A project schedule", 217, 223, "B-p215", "SARO-BMB-A-24-0018544", "audit/annex_b.md"),
    ("B-p225-227", "Attachment I project list", 225, 227, "B-p224", "SARO-BMB-A-24-0018926", "audit/annex_b.md"),
    ("B-p229-264", "Annex A project schedule", 229, 264, "B-p228", "SARO-BMB-A-24-0019575", "audit/annex_b_228_264.md"),
    ("B-p318-319", "Advice of SARO letter", 318, 319, "B-p317", "SARO-BMB-A-24-0015538", "audit/annex_b_278_338_schedule_audit.md"),
    ("B-p320", "Schedule I release of funds", 320, 320, "B-p317", "SARO-BMB-A-24-0015538", "audit/annex_b_278_338_schedule_audit.md"),
)

document_data = read("documents.json")
documents = document_data["records"]
by_id = {row["id"]: row for row in documents}
for identifier, kind, first, last, signed_id, number, audit in ATTACHMENTS:
    if identifier not in by_id:
        row = {
            "id": identifier,
            "annexId": "B",
            "type": kind,
            "pageStart": first,
            "pageEnd": last,
            "title": kind,
            "source": f"../court-documents/Annex-B-Compliance-G.R.-No.271059.pdf#page={first}",
            "audit": audit,
            "saroNumber": number,
            "relatedIds": [signed_id],
        }
        documents.append(row)
        by_id[identifier] = row
    if not by_id[identifier].get("saroNumber"):
        by_id[identifier]["saroNumber"] = number
    if signed_id not in by_id[identifier].setdefault("relatedIds", []):
        by_id[identifier]["relatedIds"].append(signed_id)
    signed = by_id[signed_id]
    if identifier not in signed.setdefault("relatedIds", []):
        signed["relatedIds"].append(identifier)

by_id["B-p349"]["missingAttachmentNote"] = "The signed SARO refers to an attached Schedule A, but Annex B ends on this page and does not contain the schedule."

documents.sort(key=lambda row: (row["annexId"], row["pageStart"], row["pageEnd"]))
write("documents.json", document_data)

saro_data = read("saros.json")
by_order = {row.get("orderDocumentId"): row for row in saro_data["records"] if row.get("orderDocumentId")}
for identifier, _, _, _, signed_id, _, _ in ATTACHMENTS:
    if identifier not in by_order[signed_id].setdefault("relatedDocumentIds", []):
        by_order[signed_id]["relatedDocumentIds"].append(identifier)
write("saros.json", saro_data)

print(f"Indexed {len(ATTACHMENTS)} Annex B related documents")
