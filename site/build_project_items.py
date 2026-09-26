"""Link visually transcribed attachment projects to their SARO and source page."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path


SITE = Path(__file__).parent
DATA = SITE / "data"
INPUTS = ("project_b_061_next.json", "project_b_63_staging.json", "project_b_65_staging.json", "project_b_67_staging.json", "project_b_72_staging.json", "project_b_74_staging.json", "project_b_76_staging.json", "project_b_78_staging.json", "project_b_80_staging.json", "project_b_82_staging.json", "project_b_84_staging.json", "project_b_093_094_next.json", "project_b_100_102_next.json", "project_b_111_113_staging.json", "project_b_118_next.json", "project_b_130_next.json", "project_b_133_next.json", "project_b_157_164.json", "project_b_159_next.json", "project_b_161_next.json", "project_b_163_next.json", "project_b_165_next.json", "project_b_171_next.json", "project_b_173_next.json", "project_b_175_next.json", "project_b_177_next.json", "project_b_179_next.json", "project_b_185_next.json", "project_b_188_194_staging.json", "project_b_195_next.json", "project_b_197_next.json", "project_b_199_next.json", "project_b_201_next.json", "project_b_203_next.json", "project_b_206.json", "project_b_208_213.json", "project_b_217_next.json", "project_b_218_next.json", "project_b_219_next.json", "project_b_220_next.json", "project_b_221_next.json", "project_b_222_next.json", "project_b_223_next.json", "project_b_224_227_staging.json", "project_b_229_next.json", "project_b_230_next.json", "project_b_235_next.json", "project_b_240_next.json", "project_b_245_next.json", "project_b_250_next.json", "project_b_255_next.json", "project_b_260_264_next.json", "project_b_269_273.json", "project_b_320_staging.json")
COMPLETE_ATTACHMENTS = {"B-p061", "B-p63", "B-p65", "B-p67", "B-p72", "B-p74", "B-p76", "B-p78", "B-p80", "B-p82", "B-p84", "B-p93-94", "B-p100-102", "B-p111-113", "B-p118-126", "B-p130-140", "B-p157-194", "B-p195-205", "B-p206", "B-p208-209", "B-p211-213", "B-p217-223", "B-p225-227", "B-p229-264", "B-p269-273", "B-p320"}
REPORTED_TOTAL_CENTAVOS = {
    "B-p061": 1_000_000_000_000,
    "B-p63": 35_062_000_000,
    "B-p65": 80_769_100_000,
    "B-p67": 46_222_000_000,
    "B-p72": 120_888_600_000,
    "B-p74": 39_484_700_000,
    "B-p76": 561_029_000_000,
    "B-p78": 2_056_559_000_000,
    "B-p80": 487_011_100_000,
    "B-p82": 1_068_062_000_000,
    "B-p84": 40_508_700_000,
    "B-p93-94": 168_039_800_000,
    "B-p100-102": 1_077_242_400_000,
    "B-p111-113": 1_191_493_500_000,
    "B-p118-126": 666_812_500_000,
    "B-p130-140": 1_202_418_400_000,
    "B-p157-194": 4_970_194_000_000,
    "B-p195-205": 1_881_800_000_000,
    "B-p206": 147_500_000_000,
    "B-p208-209": 100_000_000_000,
    "B-p211-213": 301_825_000_000,
    "B-p217-223": 998_000_000_000,
    "B-p225-227": 110_418_493_021,
    "B-p229-264": 5_134_142_000_000,
    "B-p269-273": 132_416_001_700,
    "B-p320": 875_515_865_300,
}
SIGNED_ORDER_TOTAL_CENTAVOS = {
    "B-p225-227": 110_418_493_100,
}


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def normal(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


documents = {row["id"]: row for row in read("documents.json")["records"]}
saros = read("saros.json")["records"]
by_attachment = {attachment: row for row in saros for attachment in row.get("relatedDocumentIds", [])}
by_number = defaultdict(list)
for row in saros:
    if row.get("saroNumber"):
        by_number[normal(row["saroNumber"])].append(row)

items = []
for filename in INPUTS:
    for ordinal, source in enumerate(read(filename), start=1):
        attachment = documents[source["parentDocumentId"]]
        match = by_attachment.get(attachment["id"])
        if not match:
            matches = by_number.get(normal(source.get("saroNumber") or attachment.get("saroNumber")), [])
            match = matches[0] if len(matches) == 1 else None
        signed = documents.get(match.get("orderDocumentId")) if match else None
        code = source["sourceAnnex"]
        page = source["sourcePage"]
        items.append({
            "id": f"project-{code.lower()}-p{page:03d}-{ordinal:04d}",
            "fiscalYear": match.get("fiscalYear") if match else None,
            "purposeListId": match.get("id") if match else None,
            "signedDocumentId": signed.get("id") if signed else None,
            "attachmentDocumentId": attachment["id"],
            "saroNumber": signed.get("saroNumber") if signed else source.get("saroNumber") or attachment.get("saroNumber"),
            "departmentCode": match.get("departmentCode") if match else None,
            "department": match.get("department") if match else None,
            "agency": match.get("agency") if match else None,
            "purpose": match.get("purpose") if match else None,
            "lineNumber": source.get("lineNumber"),
            "description": source["description"],
            "itemLevel": source.get("itemLevel", "project_or_claim"),
            "programPath": source.get("programPath") or [],
            "uacsCode": source.get("uacsCode"),
            "amountCentavos": source["amountCentavos"],
            "sourceAnnex": code,
            "sourcePage": page,
            "sourcePdf": f"project-pages/annex-{code.lower()}-p{page:03d}.pdf",
            "reviewNote": source.get("reviewNote"),
        })

coverage = []
for attachment_id in sorted({item["attachmentDocumentId"] for item in items}):
    pages = sorted({item["sourcePage"] for item in items if item["attachmentDocumentId"] == attachment_id})
    transcribed = sum(item["amountCentavos"] for item in items if item["attachmentDocumentId"] == attachment_id)
    entry = {"attachmentDocumentId": attachment_id, "transcribedPdfPages": pages, "complete": attachment_id in COMPLETE_ATTACHMENTS, "transcribedAmountCentavos": transcribed}
    if attachment_id in REPORTED_TOTAL_CENTAVOS:
        entry["reportedTotalCentavos"] = REPORTED_TOTAL_CENTAVOS[attachment_id]
        if entry["complete"]:
            entry["differenceCentavos"] = REPORTED_TOTAL_CENTAVOS[attachment_id] - transcribed
    if attachment_id in SIGNED_ORDER_TOTAL_CENTAVOS:
        entry["signedOrderTotalCentavos"] = SIGNED_ORDER_TOTAL_CENTAVOS[attachment_id]
        if entry["complete"]:
            entry["signedOrderDifferenceCentavos"] = SIGNED_ORDER_TOTAL_CENTAVOS[attachment_id] - transcribed
    coverage.append(entry)
payload = {"version": 1, "grain": "one lowest-level visible amount-bearing line in an attachment schedule", "coverage": coverage, "records": items}
(DATA / "project_items.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Built {len(items)} attachment project lines; {sum(bool(item['signedDocumentId']) for item in items)} linked to signed SAROs")
