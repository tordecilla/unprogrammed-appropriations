"""Publish visually transcribed Annex J release-status schedule cells."""

from __future__ import annotations

import csv
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path


DATA = Path(__file__).parent / "data"
INPUTS = ("revenue_status_2024_staging.json", "revenue_status_2025_staging.json")
records = []
ordinals = Counter()
for filename in INPUTS:
    batch = json.loads((DATA / filename).read_text(encoding="utf-8-sig"))
    year = batch["year"]
    if year not in (2024, 2025):
        raise ValueError(f"Unexpected Annex J report year: {year}")
    for source in batch["records"]:
        page = source["sourcePage"]
        if page not in ({1, 2, 3} if year == 2024 else {25}):
            raise ValueError(f"Unexpected Annex J status page: {year} p{page}")
        value = Decimal(str(source["amountPesos"]))
        if value.as_tuple().exponent < -2:
            raise ValueError(f"More than two decimal places: {year} p{page}")
        ordinals[(year, page)] += 1
        row = dict(source)
        row.update({
            "id": f"j-status-{year}-p{page:03d}-c{ordinals[(year, page)]:03d}",
            "reportYear": year,
            "sourceAnnex": "J",
            "sourcePdf": f"revenue-pages/annex-j-p{page:03d}.pdf",
            "amountPesos": format(value, "f"),
            "amountCentavos": int(value * 100),
        })
        records.append(row)

payload = {"version": 1, "grain": "one printed amount-bearing cell in an Annex J revenue release-status schedule", "records": records}
(DATA / "revenue_status.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
fields = ("id", "reportYear", "sourceAnnex", "sourcePage", "printedPage", "sourcePdf", "section", "level", "label", "agency", "saroNumber", "date", "amountType", "amountPesos", "amountCentavos", "reviewNote")
with (DATA / "revenue_status.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows({field: row.get(field) for field in fields} for row in records)
print(f"Built {len(records)} Annex J release-status cells across {len(ordinals)} source pages")
