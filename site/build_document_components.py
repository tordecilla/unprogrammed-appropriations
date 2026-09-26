"""Publish visually transcribed component cells from Annex B/H advice documents."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path


SITE = Path(__file__).parent
DATA = SITE / "data"
documents = {row["id"]: row for row in json.loads((DATA / "documents.json").read_text(encoding="utf-8"))["records"]}
inputs = (("B", "advice_components_b_300_305.json"), ("H", "annex_h_components_staging.json"))
ordinals = Counter()
rows = []
for annex, filename in inputs:
    batch = json.loads((DATA / filename).read_text(encoding="utf-8-sig"))
    for source in batch["records"]:
        document_id = source["documentId"]
        document = documents.get(document_id)
        page = source["sourcePage"]
        if not document or document["annexId"] != annex or not document["pageStart"] <= page <= document["pageEnd"]:
            raise ValueError(f"Invalid component source: {document_id} p{page}")
        value = Decimal(str(source["amountPesos"]))
        if value.as_tuple().exponent < -2:
            raise ValueError(f"More than two decimal places: {document_id} p{page}")
        ordinals[(annex, page)] += 1
        related = source.get("relatedSaroNumber") or source.get("relatedSaro") or ""
        match = re.search(r"SARO-[A-Z0-9-]+", related)
        rows.append({
            "id": f"{annex.lower()}-component-p{page:03d}-c{ordinals[(annex, page)]:03d}",
            "sourceAnnex": annex,
            "sourcePage": page,
            "sourcePdf": document["standalonePdf"],
            "documentId": document_id,
            "section": source.get("section"),
            "level": source.get("level", source.get("hierarchy")),
            "lineNumber": source.get("lineNumber"),
            "description": source.get("description") or source.get("label"),
            "amountType": source["amountType"],
            "amountPesos": format(value, "f"),
            "amountCentavos": int(value * 100),
            "relatedSaroNumber": match.group(0) if match else None,
            "reviewNote": source.get("reviewNote"),
        })

payload = {"version": 1, "grain": "one printed amount-bearing component in an Annex B/H advice document", "records": rows}
(DATA / "document_components.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
fields = tuple(rows[0])
with (DATA / "document_components.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print(f"Built {len(rows)} advice component cells across {len(ordinals)} source pages")
