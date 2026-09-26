"""Publish visually transcribed advice request and variance particulars.

These rows are separate from released SARO particulars: the source labels them
as requested amounts or variances, and one printed request row repeats another.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


DATA = Path(__file__).parent / "data"
INPUTS = ("project_b_advice_95_96.json", "project_b_advice_105.json")
PRINTED_TOTALS = {
    (95, "requested"): 3_994_875_065_655,
    (96, "variance"): 2_148_536_465_655,
    (105, "requested"): 3_496_698_500_000,
}
ADVICE_DATES = {95: "2024-06-10", 96: "2024-06-10", 105: "2024-09-17"}

records = []
for filename in INPUTS:
    for source in json.loads((DATA / filename).read_text(encoding="utf-8-sig")):
        page = source["sourcePage"]
        line = str(source["lineNumber"])
        row = {
            "id": f"advice-b-p{page:03d}-{line.replace('.', '-')}",
            "sourceAnnex": source["sourceAnnex"],
            "sourcePage": page,
            "sourcePdf": f"advice-pages/annex-b-p{page:03d}.pdf",
            "adviceDate": ADVICE_DATES[page],
            "amountStage": source["amountStage"],
            "lineNumber": line,
            "printedLineNumber": source.get("printedLineNumber", line),
            "parentLineNumber": source.get("parentLineNumber"),
            "dmsRequestReference": source.get("dmsRequestReference"),
            "description": source["description"],
            "amountCentavos": source["amountCentavos"],
            "isDuplicate": source.get("isDuplicate", False),
            "duplicateOf": source.get("duplicateOf"),
            "includeInStageTotal": source["includeInStageTotal"],
            "reviewNote": source.get("reviewNote"),
        }
        records.append(row)

ids = Counter(row["id"] for row in records)
if any(count != 1 for count in ids.values()):
    raise ValueError("Duplicate advice line ID")
coverage = []
for (page, stage), expected in PRINTED_TOTALS.items():
    subset = [row for row in records if row["sourcePage"] == page and row["amountStage"] == stage]
    eligible = [row for row in subset if row["includeInStageTotal"]]
    actual = sum(row["amountCentavos"] for row in eligible)
    if actual != expected:
        raise ValueError(f"{stage} leaves total {actual}; printed total {expected}")
    coverage.append({
        "amountStage": stage,
        "sourcePage": page,
        "sourcePages": sorted({row["sourcePage"] for row in subset}),
        "recordCount": len(subset),
        "includedRecordCount": len(eligible),
        "transcribedTotalCentavos": actual,
        "printedTotalCentavos": expected,
    })

payload = {"version": 1, "grain": "one printed advice request or variance leaf", "coverage": coverage, "records": records}
(DATA / "advice_items.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Built {len(records)} advice request/variance rows across {len({row['sourcePage'] for row in records})} pages")
