"""Publish visually transcribed Annex L summary amounts in centavos."""

from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path


DATA = Path(__file__).parent / "data"
source = json.loads((DATA / "annex_l_summary_p1.json").read_text(encoding="utf-8-sig"))
fields = source["amountColumns"]
rows = []
for ordinal, staged in enumerate(source["rows"], start=1):
    row = {
        "id": f"road-l-summary-p001-r{ordinal:02d}",
        "sourceAnnex": "L",
        "sourcePage": 1,
        "sourcePdf": "road-fund-pages/annex-l-p001.pdf",
        "fiscalYear": staged["fiscalYear"],
        "appropriationClass": staged["appropriationClass"],
        "printedUnit": "pesos",
        **{f"{field}Centavos": int(Decimal(str(staged[field])) * 100) if staged.get(field) is not None else None for field in fields},
        "remarks": staged.get("remarks"),
    }
    rows.append(row)
payload = {"version": 1, "grain": "one Annex L summary fiscal-year/appropriation-class row", "sourceNotes": source.get("notes", []), "records": rows}
(DATA / "road_fund_summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
with (DATA / "road_fund_summary.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
print(f"Built {len(rows)} Annex L summary rows")
