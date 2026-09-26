"""Publish visually transcribed Annex M agency expenditure table rows."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


SITE = Path(__file__).parent
DATA = SITE / "data"
INPUTS = (
    "annex_m_table_b9_p1.json",
    "annex_m_table_b9_p2.json",
    "annex_m_table_b9_p3.json",
    "annex_m_table_b9_p4.json",
    "annex_m_table_b9_p5.json",
    "annex_m_table_b9_p6.json",
    "annex_m_table_b9_p7.json",
    "annex_m_table_b9_p8.json",
    "annex_m_table_b9_p9.json",
    "annex_m_table_b9_p10.json",
    "annex_m_table_b9_p11.json",
    "annex_m_table_b9_p12.json",
    "annex_m_table_b9_p13.json",
    "annex_m_table_b9_p14.json",
    "annex_m_table_b9_p15.json",
    "annex_m_table_b9_p16.json",
    "annex_m_table_b9_p17.json",
    "annex_m_table_b9_p18.json",
    "annex_m_table_b9_p19.json",
    "annex_m_table_b9_p20.json",
)
AMOUNT_FIELDS = (
    "personnelServices",
    "maintenanceAndOtherOperatingExpenses",
    "capitalOutlaysAndNetLending",
    "financialExpenses",
)
rows = []
ordinals = Counter()
seen_pages = set()
for filename in INPUTS:
    batch = json.loads((DATA / filename).read_text(encoding="utf-8-sig"))
    for source in batch["rows"]:
        page = source["sourcePage"]
        seen_pages.add(page)
        ordinals[page] += 1
        for year_text, amounts in source["years"].items():
            year = int(year_text)
            row = {
                "id": f"m-b9-p{page:03d}-r{ordinals[page]:03d}-y{year}",
                "sourceAnnex": "M",
                "table": source["table"],
                "sourcePage": page,
                "printedPage": source["printedPage"],
                "sourcePdf": f"agency-expenditure-pages/annex-m-p{page:03d}.pdf",
                "particulars": source["particulars"],
                "hierarchyPath": source["hierarchyPath"],
                "rowType": source["rowType"],
                "includeInGrandTotal": source["rowType"] == "detail",
                "year": year,
                "basis": amounts["basis"],
                "unit": source["unit"],
                "currency": source["currency"],
                **{field: amounts[field] for field in AMOUNT_FIELDS},
                "total": amounts["total"],
                "reviewNote": source.get("reviewNote"),
            }
            if row["unit"] != "thousand pesos" or any(not isinstance(row[field], int) for field in (*AMOUNT_FIELDS, "total")):
                raise ValueError(f"Invalid amount/unit in {row['id']}")
            difference = sum(row[field] for field in AMOUNT_FIELDS) - row["total"]
            if difference and not row["reviewNote"]:
                raise ValueError(f"Printed row arithmetic differs without review note: {row['id']} ({difference})")
            rows.append(row)

reconciliation = []
for year in (2024, 2025, 2026):
    printed = next((row for row in rows if row["sourcePage"] == 19 and row["rowType"] == "grandTotal" and row["year"] == year), None)
    if printed:
        detail = [row for row in rows if row["includeInGrandTotal"] and row["year"] == year]
        differences = {field: sum(row[field] for row in detail) - printed[field] for field in (*AMOUNT_FIELDS, "total")}
        reconciliation.append({
            "year": year,
            "printedGrandTotalSourcePage": 19,
            "detailRecordCount": len(detail),
            "detailMinusPrintedThousandPesos": differences,
            "status": "exact" if not any(differences.values()) else "unresolved row-sum versus printed-grand-total difference",
        })

payload = {"version": 1, "grain": "one Annex M printed agency/hierarchy row per fiscal year", "transcribedPdfPages": sorted(seen_pages), "reconciliation": reconciliation, "reconciliationNote": "annex_m_reconciliation_note.md", "records": rows}
(DATA / "agency_expenditure.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
fields = [key for key in rows[0] if key != "hierarchyPath"]
fields.insert(fields.index("rowType"), "hierarchyPath")
with (DATA / "agency_expenditure.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({**row, "hierarchyPath": " > ".join(row["hierarchyPath"])})
print(f"Built {len(rows)} Annex M row-year records across {len(seen_pages)} pages")
