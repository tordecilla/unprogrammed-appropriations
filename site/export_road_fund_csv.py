"""Export visually transcribed Annex L project fiscal rows as CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path


SITE = Path(__file__).parent
rows = json.loads((SITE / "data" / "road_fund_projects.json").read_text(encoding="utf-8"))["records"]
fields = (
    "id", "sourceAnnex", "sourcePage", "printedPage", "sourcePdf",
    "scheduleNumber", "fiscalYear", "appropriationType", "asOfDate",
    "lineNumber", "uacsCode", "description", "operatingUnit",
    "authorizedAppropriationCentavos", "beginningBalanceCentavos", "gaaaoCentavos", "fisaroCentavos",
    "totalAllotmentsCentavos", "obligationsCentavos",
    "disbursementsCentavos", "unobligatedBalanceCentavos",
    "unpaidObligationsCentavos", "reviewNote",
)
path = SITE / "data" / "road_fund_projects.csv"
with path.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
print(f"Exported {len(rows)} Annex L project lines to {path}")
