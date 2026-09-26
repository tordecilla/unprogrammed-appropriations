"""Publish visually transcribed Annex J revenue evidence without treating it as releases."""

from __future__ import annotations

import csv
import json
from decimal import Decimal
from pathlib import Path


SITE = Path(__file__).parent
DATA = SITE / "data"
INPUTS = ("annex_j_certificates_p4_10.json", "annex_j_certificates_p11_17.json", "annex_j_certificates_p18_24.json", "annex_j_certificates_p26_28.json")

documents = []
seen = set()
for filename in INPUTS:
    batch = json.loads((DATA / filename).read_text(encoding="utf-8-sig"))
    for source in batch["documents"]:
        document = dict(source)
        page = document["sourcePage"]
        if not 1 <= page <= 28 or document["documentId"] in seen:
            raise ValueError(f"Invalid or duplicate Annex J document: {document['documentId']}")
        seen.add(document["documentId"])
        document["sourceAnnex"] = "J"
        document["sourcePdf"] = f"revenue-pages/annex-j-p{page:03d}.pdf"
        for amount in document.get("certifiedAmounts", []) + document.get("reportedAmounts", []):
            value = Decimal(str(amount.get("amountPesos")))
            if value < 0 or value.as_tuple().exponent < -2:
                raise ValueError(f"Invalid amount in {document['documentId']}")
            if amount.get("amountType") == "release":
                raise ValueError(f"Revenue evidence misclassified as release: {document['documentId']}")
        documents.append(document)

documents.sort(key=lambda row: row["sourcePage"])
output = {"version": 1, "grain": "one visually identified revenue-evidence document", "records": documents}
(DATA / "revenue_evidence.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

headings = (
    "id", "document_id", "source_annex", "source_page", "source_pdf", "document_type", "issuer",
    "document_date", "covered_period", "collection_category", "recipient_or_destination",
    "remittance_date_or_period", "amount_group", "amount_type", "amount_pesos", "amount_period", "tranche",
    "signature_name", "signature_title", "visible_signature", "visible_stamp", "review_notes",
)
rows = []
for document in documents:
    amounts = [("certified", amount) for amount in document.get("certifiedAmounts", [])] + [("reported", amount) for amount in document.get("reportedAmounts", [])]
    for index, (group, amount) in enumerate(amounts, 1):
        signature = document.get("signature") or {}
        rows.append({
            "id": f"{document['documentId']}-{index}",
            "document_id": document["documentId"],
            "source_annex": "J",
            "source_page": document["sourcePage"],
            "source_pdf": document["sourcePdf"],
            "document_type": document.get("documentType"),
            "issuer": document.get("issuer"),
            "document_date": document.get("documentDate"),
            "covered_period": document.get("coveredPeriod"),
            "collection_category": document.get("collectionCategory"),
            "recipient_or_destination": document.get("recipientOrDestination"),
            "remittance_date_or_period": document.get("remittanceDateOrPeriod"),
            "amount_group": group,
            "amount_type": amount.get("amountType"),
            "amount_pesos": amount.get("amountPesos"),
            "amount_period": amount.get("period"),
            "tranche": amount.get("tranche"),
            "signature_name": signature.get("name"),
            "signature_title": signature.get("title"),
            "visible_signature": signature.get("visibleSignature"),
            "visible_stamp": signature.get("visibleStamp"),
            "review_notes": document.get("reviewNotes"),
        })
with (DATA / "revenue_evidence.csv").open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=headings)
    writer.writeheader()
    writer.writerows(rows)
print(f"Published {len(documents)} Annex J evidence documents and {len(rows)} amount rows")
