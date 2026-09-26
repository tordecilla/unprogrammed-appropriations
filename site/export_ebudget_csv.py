"""Export the visually transcribed eBudget transaction catalog as CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path


SITE = Path(__file__).parent
rows = json.loads((SITE / "data" / "ebudget_transactions.json").read_text(encoding="utf-8"))["records"]
fields = (
    "id", "fiscalYear", "sourceAnnex", "sourcePage", "printedPage", "sourcePdf",
    "fundingSourceCode", "saroNumber", "barcodeNumber", "issueDate", "department",
    "sourceDepartment", "agency", "sourceAgency", "organizationPath", "particulars",
    "purpose", "psCentavos", "mooeCentavos", "finexCentavos", "coCentavos",
    "totalCentavos", "saroType", "status", "statusDate", "legalCode",
    "appropriationSource", "fundingCode", "fundCodeSource", "fundCodeRecipient",
    "purposeListId", "signedDocumentId", "reviewNote",
)
path = SITE / "data" / "ebudget_transactions.csv"
with path.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        record = dict(row)
        record["organizationPath"] = " > ".join(row.get("organizationPath") or [])
        writer.writerow(record)
print(f"Exported {len(rows)} eBudget transactions to {path}")
