"""Merge visual SARO-form transcriptions into structured document/line data."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


DATA = Path(__file__).parent / "data"


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def normal(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


catalog = read("documents.json")
documents = {row["id"]: row for row in catalog["records"]}
lines = []
seen = set()
warnings = []
field_names = {
    "department": "formDepartment",
    "agency": "formAgency",
    "operatingUnit": "formOperatingUnit",
    "locality": "formLocality",
    "orgCode": "formOrgCode",
    "fundingSource": "fundingSource",
    "fundingSourceCode": "fundingSourceCode",
    "formPurpose": "formPurpose",
    "totalAmountPesos": "formAmountPesos",
    "validUntil": "validUntil",
    "reviewNote": "particularsReviewNote",
    "formStatusNote": "formStatusNote",
}

selected = set(sys.argv[1:])
for filename in ("particulars_b_early.json", "particulars_b_127.json", "particulars_b_late.json", "particulars_b_gap_275_314.json", "particulars_h.json"):
    if selected and filename not in selected:
        continue
    if not (DATA / filename).exists():
        continue
    for transcription in read(filename):
        doc_id = transcription["documentId"]
        document = documents.get(doc_id)
        if not document or document["type"] != "SARO":
            raise ValueError(f"{filename}: unknown signed SARO {doc_id}")
        if doc_id in seen:
            raise ValueError(f"Duplicate SARO transcription: {doc_id}")
        seen.add(doc_id)
        if normal(document.get("saroNumber")) != normal(transcription.get("saroNumber")):
            raise ValueError(f"{doc_id}: visual transcription number differs from index")
        if document["pageStart"] != transcription["pageStart"]:
            raise ValueError(f"{doc_id}: source page differs from index")
        for incoming, outgoing in field_names.items():
            if incoming in transcription:
                document[outgoing] = transcription[incoming]
        total = transcription.get("totalAmountPesos")
        if isinstance(total, int):
            old_total = document.get("amountPesos")
            if old_total is not None and old_total != total:
                warnings.append(f"{doc_id}: previously indexed amount {old_total} differs from form {total}")
            else:
                document["amountPesos"] = total
                document["amountStage"] = transcription.get("amountStage") or "released"
        for index, particular in enumerate(transcription.get("particulars") or [], start=1):
            lines.append({
                "id": f"{doc_id}-line-{index:02d}",
                "documentId": doc_id,
                "saroNumber": document.get("saroNumber"),
                "sourceAnnex": document["annexId"],
                "sourcePage": particular.get("sourcePage", document["pageStart"]),
                "lineNumber": index,
                "mfoPapCode": particular.get("mfoPapCode"),
                "description": particular.get("description"),
                "programPath": particular.get("programPath") or [],
                "objectCode": particular.get("objectCode"),
                "amountPesos": particular.get("amountPesos"),
                "note": particular.get("note"),
                "standalonePdf": document.get("standalonePdf"),
                "adviceParticular": particular.get("adviceParticular"),
                "adviceSourcePage": particular.get("adviceSourcePage"),
                "adviceSourcePdf": particular.get("adviceSourcePdf"),
            })

catalog["records"].sort(key=lambda row: (row["annexId"], row["pageStart"], row["id"]))
(DATA / "documents.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(DATA / "particulars.json").write_text(json.dumps({"version": 1, "grain": "one lowest-level amount-bearing line in a signed SARO", "records": lines}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Merged {len(seen)} signed SARO forms and {len(lines)} particular lines")
for warning in warnings:
    print("-", warning)
