"""Publish visually transcribed debt-service reference rows from Annexes N-P."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


DATA = Path(__file__).parent / "data"
rows = []
ordinals = Counter()


def append(code: str, page: int, year: int, *, series: str, particulars: str, row_type: str,
           hierarchy: list[str], printed_unit: str, amount: int, domestic: int | None = None,
           foreign: int | None = None, component: str | None = None, market: str | None = None,
           review_note: str | None = None):
    ordinals[(code, page, year)] += 1
    precision = 1_000_000 if printed_unit == "million pesos" else 1
    rows.append({
        "id": f"debt-{code.lower()}-p{page:03d}-y{year}-r{ordinals[(code, page, year)]:03d}",
        "sourceAnnex": code,
        "sourcePage": page,
        "sourcePdf": f"debt-pages/annex-{code.lower()}-p{page:03d}.pdf",
        "year": year,
        "series": series,
        "particulars": particulars,
        "rowType": row_type,
        "hierarchyPath": hierarchy,
        "component": component,
        "market": market,
        "printedUnit": printed_unit,
        "printedAmount": amount,
        "amountPesos": amount * precision,
        "precisionPesos": precision,
        "domesticPrintedAmount": domestic,
        "foreignPrintedAmount": foreign,
        "domesticPesos": domestic * precision if domestic is not None else None,
        "foreignPesos": foreign * precision if foreign is not None else None,
        "reviewNote": review_note,
    })


n = json.loads((DATA / "annex_n_debt_service_p1.json").read_text(encoding="utf-8-sig"))
for source in n["rows"]:
    append("N", 1, 2024, series="2024 principal amortization appropriation", particulars=source["particulars"],
           row_type="grandTotal" if source["particulars"].upper() == "TOTAL" else "detail",
           hierarchy=[source["particulars"]], printed_unit="pesos", amount=source["total"],
           review_note=n.get("reviewNote"))

for page in (1, 2):
    o = json.loads((DATA / f"annex_o_debt_service_p{page}.json").read_text(encoding="utf-8-sig"))
    for source in o["rows"]:
        for year_text, amount in source["years"].items():
            hierarchy = source.get("hierarchyPath") or [source["particulars"]]
            market = next(("domestic" if label.lower() == "domestic" else "foreign" for label in hierarchy if label.lower() in {"domestic", "foreign", "external"}), None)
            append("O", page, int(year_text), series="historical debt service", particulars=source["particulars"],
                   row_type=source["rowType"], hierarchy=hierarchy,
                   printed_unit="million pesos", amount=amount,
                   component=source.get("component"), market=market,
                   review_note=source.get("reviewNote") or o.get("reviewNote"))

p = json.loads((DATA / "annex_p_debt_service_p1.json").read_text(encoding="utf-8-sig"))
for source in p["rows"]:
    for year_text in map(str, p["years"]):
        value = source[year_text]
        difference = value["domestic"] + value["foreign"] - value["total"]
        note = source.get("reviewNote") or (f"Printed domestic plus foreign differs from total by {difference:+d} million pesos." if difference else None)
        append("P", 1, int(year_text), series="2024-2026 debt service outlook", particulars=source["particulars"],
               row_type=source["rowType"], hierarchy=source.get("hierarchyPath") or [source["particulars"]],
               printed_unit="million pesos", amount=value["total"], domestic=value["domestic"],
               foreign=value["foreign"], component=(source.get("hierarchyPath") or [source["particulars"]])[0], review_note=note)

payload = {"version": 1, "grain": "one printed debt-service category or instrument and year", "reconciliationNote": "debt_reference_reconciliation_note.md", "records": rows}
(DATA / "debt_reference.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
fields = [key for key in rows[0] if key != "hierarchyPath"]
fields.insert(fields.index("printedUnit"), "hierarchyPath")
with (DATA / "debt_reference.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({**row, "hierarchyPath": " > ".join(row["hierarchyPath"])})
print(f"Built {len(rows)} debt-reference rows across {len({(r['sourceAnnex'], r['sourcePage']) for r in rows})} pages")
