"""Apply separately reviewed page-image transcriptions to the document registry."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


DATA = Path(__file__).parent / "data"


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def date_iso(value: str | None) -> str | None:
    if not value:
        return None
    for format_string in ("%Y-%m-%d", "%B %d, %Y"):
        try:
            return datetime.strptime(value, format_string).date().isoformat()
        except ValueError:
            pass
    return value


registry = read("documents.json")
by_id = {record["id"]: record for record in registry["records"]}
updates = read("h_order_fields.json") + [dict(id=key, **value) for key, value in read("b_order_fields.json")["records"].items()]

for update in updates:
    record_id = update["id"]
    if record_id not in by_id:
        if update.get("registryStatus") != "not indexed in documents.json":
            raise ValueError(f"Unindexed visual transcription: {record_id}")
        page = update["sourcePage"]
        by_id[record_id] = {
            "id": record_id,
            "annexId": "B",
            "type": "SARO",
            "pageStart": page,
            "pageEnd": page,
            "title": "SARO",
            "source": f"../court-documents/Annex-B-Compliance-G.R.-No.271059.pdf#page={page}",
            "audit": f"audit/annex_b.md; visually checked PDF p. {page}",
        }
    record = by_id[record_id]
    for field in ("saroNumber", "saroNumbers", "agency", "purpose", "amountPesos", "amountBreakdown", "ambiguities"):
        if field in update:
            record[field] = update[field]
    if update.get("date"):
        record["date"] = date_iso(update["date"])
    if record["type"] == "SARO" and update.get("amountPesos") is not None:
        record["amountStage"] = "released"

registry["records"] = sorted(by_id.values(), key=lambda record: (record["annexId"], record["pageStart"], record["id"]))
registry["scope"] = "Individually bounded Annex B, H, and J records identified in visual audit notes or reviewed page images"
registry["completeness"] = "partial_initial_registry"
registry["completenessNote"] = "The Annex B and J packets are not completely segmented. Only individually bounded records are indexed; Annex J certificates remain grouped in the audit notes."
(DATA / "documents.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"{len(registry['records'])} document records")
