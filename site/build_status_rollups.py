"""Publish visually transcribed UA status-report summary cells.

Rollups are kept apart from numbered SARO rows to avoid double counting.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


DATA = Path(__file__).parent / "data"
INPUTS = ("status_f_rollups_1_3_4.json", "status_c_rollups_1_3_staging.json")
VARIOUS_INPUTS = ("status_f_17_20_various_notes.json", "status_f_21_24_various_notes.json", "status_f_25_28_various_notes.json", "status_f_29_34_various_notes.json", "status_c_4_15_rollups.json", "status_c_16_19_rollups.json", "status_c_20_23_rollups.json", "status_c_24_27_rollups.json", "status_c_28_31_rollups.json", "status_c_32_35_rollups.json", "status_c_36_39_rollups.json", "status_c_40_55_rollups.json", "status_c_56_59_rollups.json", "status_c_60_63_rollups.json", "status_c_64_67_rollups.json", "status_c_68_71_rollups.json", "status_c_72_79_rollups.json", "status_c_80_99_rollups.json", "status_c_100_105_rollups.json", "status_c_106_111_rollups.json", "status_c_112_119_various_notes.json", "status_c_120_127_various_notes.json", "status_c_128_135_various_notes.json")
rows = []
ordinals = Counter()
for filename in INPUTS:
    staged = json.loads((DATA / filename).read_text(encoding="utf-8-sig"))
    for source in staged["records"]:
        code = source["annexId"].upper()
        page = source["sourcePage"]
        unit = source["unit"]
        if unit not in {"pesos", "thousand pesos"}:
            raise ValueError(f"Unexpected status rollup unit: {unit}")
        ordinals[(code, page)] += 1
        rows.append({
            "id": f"{code.lower()}-status-rollup-p{page:03d}-c{ordinals[(code, page)]:03d}",
            "fiscalYear": 2025 if code == "F" else 2024,
            "sourceAnnex": code,
            "sourcePage": page,
            "printedPage": source["printedPage"],
            "sourcePdf": f"status-pages/annex-{code.lower()}-p{page:03d}.pdf",
            "scope": source["scope"],
            "category": source["category"],
            "measure": source["measure"],
            "expenseClass": source["expenseClass"],
            "printedAmount": source["amount"],
            "printedUnit": unit,
            "amountPesos": source["amount"] * (1000 if unit == "thousand pesos" else 1),
            "precisionPesos": 1000 if unit == "thousand pesos" else 1,
            "reviewNote": source.get("reviewNote") or None,
        })

for filename in VARIOUS_INPUTS:
    staged = json.loads((DATA / filename).read_text(encoding="utf-8-sig"))
    for source in staged["records"]:
        code = source["annexId"].upper()
        page = source["sourcePage"]
        for expense_class, amount in source["amounts"].items():
            ordinals[(code, page)] += 1
            rows.append({
                "id": f"{code.lower()}-status-rollup-p{page:03d}-c{ordinals[(code, page)]:03d}",
                "fiscalYear": 2025 if code == "F" else 2024,
                "sourceAnnex": code,
                "sourcePage": page,
                "printedPage": source["printedPage"],
                "sourcePdf": f"status-pages/annex-{code.lower()}-p{page:03d}.pdf",
                "scope": f"{source['agency']} / {source['scope']}",
                "category": source["category"],
                "measure": "Allotment Releases",
                "expenseClass": expense_class,
                "printedAmount": amount,
                "printedUnit": source["unit"],
                "amountPesos": amount,
                "precisionPesos": 1,
                "reviewNote": "Unnumbered aggregate; not a distinct SARO instrument." + (f" {source['reviewNote']}" if source.get("reviewNote") else ""),
            })

seen_cells = set()
for row in rows:
    key = tuple(row[field] for field in ("sourceAnnex", "sourcePage", "printedPage", "scope", "category", "measure", "expenseClass", "printedAmount", "printedUnit"))
    if key in seen_cells:
        raise ValueError(f"Duplicate status summary cell: {key}")
    seen_cells.add(key)

payload = {"version": 1, "grain": "one printed UA status-report summary cell", "records": rows}
(DATA / "status_rollups.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
fields = list(rows[0])
with (DATA / "status_rollups.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print(f"Built {len(rows)} status rollup cells across {len(ordinals)} source pages")
