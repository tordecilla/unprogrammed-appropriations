"""Index visually transcribed signed SAROs found in Annex B page gaps."""

from __future__ import annotations

import json
import re
from pathlib import Path


DATA = Path(__file__).parent / "data"
STAGING = DATA / "particulars_b_gap_275_314.json"
CATALOG = DATA / "documents.json"

staged = json.loads(STAGING.read_text(encoding="utf-8-sig"))
catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
documents = catalog["records"]
by_id = {row["id"]: row for row in documents}
STATUS_EVIDENCE = {
    "B-p275-276": [{"sourcePage": 277, "sourcePdf": "advice-pages/annex-b-p277.pdf", "label": "Issued-SARO advice"}],
    "B-p308": [{"sourcePage": 309, "sourcePdf": "advice-pages/annex-b-p309.pdf", "label": "Issued-SARO advice"}],
}
for item in staged:
    identifier = item["documentId"]
    page = item["pageStart"]
    end = item.get("pageEnd", page)
    number = item["saroNumber"]
    if not re.fullmatch(r"SARO-[A-Z0-9-]+", number):
        raise ValueError(f"{identifier}: invalid SARO number")
    if identifier in by_id:
        current = by_id[identifier]
        if (current["pageStart"], current["pageEnd"], current.get("saroNumber")) != (page, end, number):
            raise ValueError(f"{identifier}: existing document conflicts with visual transcription")
        if identifier in STATUS_EVIDENCE:
            current["statusEvidence"] = STATUS_EVIDENCE[identifier]
        continue
    document = {
        "id": identifier,
        "annexId": "B",
        "type": "SARO",
        "pageStart": page,
        "pageEnd": end,
        "title": "SARO",
        "source": f"../court-documents/Annex-B-Compliance-G.R.-No.271059.pdf#page={page}",
        "audit": "audit/annex_b_gap_pages_274_316.md",
        "saroNumber": number,
        "date": item["dateOfIssue"],
        "agency": item["agency"],
        "purpose": item["formPurpose"],
        "boundaryReview": "visual; form watermark/status requires review",
        "amountPesos": item["totalAmountPesos"],
        "amountStage": item["amountStage"],
        "formStatusNote": item["formStatusNote"],
        "statusEvidence": STATUS_EVIDENCE.get(identifier, []),
    }
    documents.append(document)
    by_id[identifier] = document

documents.sort(key=lambda row: (row["annexId"], row["pageStart"], row["id"]))
CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Indexed {len(staged)} visually identified Annex B SARO forms")
