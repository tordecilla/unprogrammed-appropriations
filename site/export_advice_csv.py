"""Export source-qualified advice request and variance leaves as CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path


DATA = Path(__file__).parent / "data"
rows = json.loads((DATA / "advice_items.json").read_text(encoding="utf-8"))["records"]
fields = (
    "id", "sourceAnnex", "sourcePage", "sourcePdf", "adviceDate",
    "amountStage", "lineNumber", "printedLineNumber", "parentLineNumber", "dmsRequestReference", "description",
    "amountCentavos", "isDuplicate", "duplicateOf", "includeInStageTotal", "reviewNote",
)
path = DATA / "advice_items.csv"
with path.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
print(f"Exported {len(rows)} advice request/variance rows to {path}")
