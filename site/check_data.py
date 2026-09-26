"""Check cross-record links and source ranges in the published JSON catalogs."""

from __future__ import annotations

import json
import re
import csv
from collections import Counter
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).parent
DATA = ROOT / "data"
errors: list[str] = []


def read(name: str):
    path = DATA / name
    text = path.read_text(encoding="utf-8")
    if text.startswith("\ufeff") or "\ufffd" in text:
        errors.append(f"{name}: BOM or replacement character")
    return json.loads(text)


def unique(name: str, rows: list[dict]) -> dict[str, dict]:
    ids = [row["id"] for row in rows]
    for identifier, count in Counter(ids).items():
        if count != 1:
            errors.append(f"{name}: duplicate {identifier}")
    return {row["id"]: row for row in rows}


def normal(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


sources = read("annexes.json")["records"]
documents = read("documents.json")["records"]
saros = read("saros.json")["records"]
particulars = read("particulars.json")["records"]
project_data = read("project_items.json")
projects = project_data["records"]
listing_data = read("ebudget_transactions.json")
listings = listing_data["records"]
advice_data = read("advice_items.json")
advice_items = advice_data["records"]
document_components = read("document_components.json")["records"]
road_data = read("road_fund_projects.json")
road_projects = road_data["records"]
road_summary = read("road_fund_summary.json")["records"]
agency_data = read("agency_expenditure.json")
agency_expenditure = agency_data["records"]
process_steps = read("process_steps.json")["records"]
debt_data = read("debt_reference.json")
debt_reference = debt_data["records"]
revenue_data = read("revenue_evidence.json")
revenue_documents = revenue_data["records"]
revenue_status = read("revenue_status.json")["records"]
status_rows = read("status_rows.json")["records"]
status_allocations = read("status_allocations.json")["records"]
status_rollups = read("status_rollups.json")["records"]
status_notes = read("status_report_notes.json")["records"]
schemas = read("datasets.json")["records"]
discrepancies = read("discrepancies.json")["records"]
unique("sources", sources)
document_ids = unique("documents", documents)
unique("saros", saros)
unique("particulars", particulars)
unique("project items", projects)
unique("eBudget transactions", listings)
unique("advice request/variance items", advice_items)
unique("advice document components", document_components)
unique("road-fund projects", road_projects)
unique("road-fund summary", road_summary)
unique("agency expenditure rows", agency_expenditure)
unique("release process entries", process_steps)
unique("debt reference rows", debt_reference)
if len({row["documentId"] for row in revenue_documents}) != len(revenue_documents):
    errors.append("revenue evidence: duplicate document ID")
unique("revenue status cells", revenue_status)
with (DATA / "ebudget_transactions.csv").open(encoding="utf-8-sig", newline="") as stream:
    listing_csv_ids = [row["id"] for row in csv.DictReader(stream)]
if listing_csv_ids != [row["id"] for row in listings]:
    errors.append("eBudget CSV differs from JSON transaction catalog")
with (DATA / "advice_items.csv").open(encoding="utf-8-sig", newline="") as stream:
    advice_csv_ids = [row["id"] for row in csv.DictReader(stream)]
if advice_csv_ids != [row["id"] for row in advice_items]:
    errors.append("Advice CSV differs from JSON request/variance catalog")
with (DATA / "document_components.csv").open(encoding="utf-8-sig", newline="") as stream:
    component_csv_ids = [row["id"] for row in csv.DictReader(stream)]
if component_csv_ids != [row["id"] for row in document_components]:
    errors.append("Advice component CSV differs from JSON")
if {(row["sourceAnnex"], row["sourcePage"]) for row in document_components} != {("B", 300), ("B", 304), ("H", 2), ("H", 6)}:
    errors.append("Annex B/H advice component page coverage differs from audited pages")
for row in document_components:
    if row["documentId"] not in document_ids or not (ROOT / row["sourcePdf"]).is_file():
        errors.append(f"{row['id']}: missing advice document link")
    if int(Decimal(row["amountPesos"]) * 100) != row["amountCentavos"]:
        errors.append(f"{row['id']}: peso/centavo conversion differs")
with (DATA / "road_fund_projects.csv").open(encoding="utf-8-sig", newline="") as stream:
    road_csv_ids = [row["id"] for row in csv.DictReader(stream)]
if road_csv_ids != [row["id"] for row in road_projects]:
    errors.append("Road-fund CSV differs from JSON project catalog")
with (DATA / "road_fund_summary.csv").open(encoding="utf-8-sig", newline="") as stream:
    road_summary_csv_ids = [row["id"] for row in csv.DictReader(stream)]
if road_summary_csv_ids != [row["id"] for row in road_summary]:
    errors.append("Road-fund summary CSV differs from JSON")
with (DATA / "agency_expenditure.csv").open(encoding="utf-8-sig", newline="") as stream:
    agency_csv_ids = [row["id"] for row in csv.DictReader(stream)]
if agency_csv_ids != [row["id"] for row in agency_expenditure]:
    errors.append("Agency-expenditure CSV differs from JSON")
with (DATA / "debt_reference.csv").open(encoding="utf-8-sig", newline="") as stream:
    debt_csv_ids = [row["id"] for row in csv.DictReader(stream)]
if debt_csv_ids != [row["id"] for row in debt_reference]:
    errors.append("Debt-reference CSV differs from JSON")
with (DATA / "revenue_evidence.csv").open(encoding="utf-8-sig", newline="") as stream:
    revenue_csv = list(csv.DictReader(stream))
if len(revenue_csv) != sum(len(row.get("certifiedAmounts", [])) + len(row.get("reportedAmounts", [])) for row in revenue_documents):
    errors.append("Revenue-evidence CSV row count differs from JSON")
with (DATA / "revenue_status.csv").open(encoding="utf-8-sig", newline="") as stream:
    revenue_status_csv_ids = [row["id"] for row in csv.DictReader(stream)]
if revenue_status_csv_ids != [row["id"] for row in revenue_status]:
    errors.append("Revenue-status CSV differs from JSON")
if {row["sourcePage"] for row in revenue_status} != {1, 2, 3, 25}:
    errors.append("Annex J release-status page coverage differs from audited pages")
for row in revenue_status:
    if row["sourceAnnex"] != "J" or not (ROOT / row["sourcePdf"]).is_file():
        errors.append(f"{row['id']}: missing one-page Annex J status source")
    if int(Decimal(row["amountPesos"]) * 100) != row["amountCentavos"]:
        errors.append(f"{row['id']}: peso/centavo conversion differs")
for year, label, section, expected in (
    (2024, "Excess Income", "Summary; column=total", "396989182236.26"),
    (2024, "Less: SARO Releases", "Summary; column=total", "391319793599.00"),
    (2024, "Balance", "Summary; column=total", "5669388637.26"),
    (2025, "Available Excess Income per BTr Certifications", "available_income", "102277458303.18"),
    (2025, "Less: SARO Releases", "saro_releases", "101566373729.00"),
    (2025, "Balance", "summary", "711084574.18"),
):
    selected = [row for row in revenue_status if row["reportYear"] == year and row["label"] == label and row["section"] == section]
    if len(selected) != 1 or Decimal(selected[0]["amountPesos"]) != Decimal(expected):
        errors.append(f"Annex J {year} {label} total differs from visually checked schedule")
for row in revenue_documents:
    if row.get("sourceAnnex") != "J" or not 1 <= row["sourcePage"] <= 28 or not (ROOT / row["sourcePdf"]).is_file():
        errors.append(f"{row['documentId']}: invalid Annex J page source")
    for amount in row.get("certifiedAmounts", []) + row.get("reportedAmounts", []):
        if not isinstance(amount.get("amountPesos"), (int, float)) or amount["amountPesos"] < 0 or amount.get("amountType") == "release":
            errors.append(f"{row['documentId']}: invalid certified amount or release classification")
revenue_by_id = {row["documentId"]: row for row in revenue_documents}
def revenue_amount(document_id: str, period: str | None = None) -> Decimal:
    amounts = revenue_by_id[document_id].get("certifiedAmounts", []) + revenue_by_id[document_id].get("reportedAmounts", [])
    selected = [amount for amount in amounts if period is None or amount.get("period") == period]
    if len(selected) != 1:
        errors.append(f"{document_id}: expected one revenue amount for {period}")
        return Decimal(0)
    return Decimal(str(selected[0]["amountPesos"]))
if revenue_amount("J-p24", "2023 Q4") - revenue_amount("J-p20", "2023 Q4") != Decimal("0.03"):
    errors.append("Annex J Q4 rice-duty source difference changed")
for document_id, expected in {
    "J-p26": "106529682065.94", "J-p27": "41295050745.42", "J-p28": "9252725491.82",
}.items():
    if revenue_amount(document_id) != Decimal(expected):
        errors.append(f"{document_id}: 2025 certificate differs from visually checked p25 amount")
status_ids = unique("status rows", status_rows)
unique("status allocations", status_allocations)
unique("status rollups", status_rollups)
unique("status report notes", status_notes)
unique("schemas", schemas)
unique("source discrepancies", discrepancies)
for item in discrepancies:
    if not item.get("verification"):
        errors.append(f"{item['id']}: missing verification status")
    if not item.get("sources"):
        errors.append(f"{item['id']}: no source links")
    for source in item.get("sources", []):
        if not (ROOT / source["href"]).is_file():
            errors.append(f"{item['id']}: missing linked source {source['href']}")
source_codes = {row["id"].removeprefix("annex-").upper(): row for row in sources}

for row in sources:
    for field in ("pdfUrl", "audit"):
        if not (ROOT / row[field]).exists():
            errors.append(f"{row['id']}: missing {field} file")
    if row["pages"] < 1:
        errors.append(f"{row['id']}: invalid page count")

for row in documents:
    code = row["annexId"]
    source = source_codes.get(code)
    if not source or not 1 <= row["pageStart"] <= row["pageEnd"] <= source["pages"]:
        errors.append(f"{row['id']}: invalid source/page span")
    for related in row.get("relatedIds", []):
        if related not in document_ids:
            errors.append(f"{row['id']}: unknown related document {related}")
    if row.get("duplicateOf") and row["duplicateOf"] not in document_ids:
        errors.append(f"{row['id']}: unknown duplicate source {row['duplicateOf']}")
    if row.get("possibleDuplicateOf") and row["possibleDuplicateOf"] not in document_ids:
        errors.append(f"{row['id']}: unknown possible duplicate source {row['possibleDuplicateOf']}")
    if row.get("amountPesos") is not None and (not isinstance(row["amountPesos"], int) or row["amountPesos"] < 0):
        errors.append(f"{row['id']}: invalid peso amount")
    if row.get("standalonePdf"):
        exported = ROOT / row["standalonePdf"]
        if not exported.is_file() or exported.stat().st_size < 100:
            errors.append(f"{row['id']}: missing standalone PDF")
    for evidence in row.get("statusEvidence", []):
        if not source or not 1 <= evidence["sourcePage"] <= source["pages"] or not (ROOT / evidence["sourcePdf"]).is_file():
            errors.append(f"{row['id']}: invalid or missing status evidence page")

lines_by_document: dict[str, list[dict]] = {}
for line in particulars:
    parent = document_ids.get(line["documentId"])
    if not parent or parent["type"] != "SARO":
        errors.append(f"{line['id']}: missing signed SARO parent")
        continue
    if normal(line.get("saroNumber")) != normal(parent.get("saroNumber")):
        errors.append(f"{line['id']}: SARO number differs from parent")
    if not parent["pageStart"] <= line["sourcePage"] <= parent["pageEnd"]:
        errors.append(f"{line['id']}: particular source page outside signed form")
    if line.get("amountPesos") is not None and (not isinstance(line["amountPesos"], int) or line["amountPesos"] < 0):
        errors.append(f"{line['id']}: invalid particular amount")
    if line.get("adviceParticular"):
        if not line.get("adviceSourcePage") or not (ROOT / line.get("adviceSourcePdf", "")).is_file():
            errors.append(f"{line['id']}: missing advice evidence page")
        if line["sourceAnnex"] != "B" or not 1 <= line["adviceSourcePage"] <= source_codes["B"]["pages"]:
            errors.append(f"{line['id']}: invalid advice evidence source page")
    lines_by_document.setdefault(parent["id"], []).append(line)

for identifier in ("B-p275-276", "B-p308", "B-p314"):
    form = document_ids.get(identifier)
    if form and (form.get("amountStage") != "status_unresolved" or "CANCELLED" not in (form.get("formStatusNote") or "")):
        errors.append(f"{identifier}: unresolved cancellation status not preserved")

for doc_id, lines in lines_by_document.items():
    parent = document_ids[doc_id]
    total = parent.get("formAmountPesos")
    if total is not None and all(isinstance(line.get("amountPesos"), int) for line in lines):
        line_total = sum(line["amountPesos"] for line in lines)
        if line_total != total:
            errors.append(f"{doc_id}: particular lines total {line_total}, signed SARO total {total}")

projects_by_attachment: dict[str, list[dict]] = {}
for item in projects:
    attachment = document_ids.get(item["attachmentDocumentId"])
    signed = document_ids.get(item.get("signedDocumentId"))
    source = source_codes.get(item["sourceAnnex"])
    if not attachment or not source or attachment["annexId"] != item["sourceAnnex"] or not attachment["pageStart"] <= item["sourcePage"] <= attachment["pageEnd"]:
        errors.append(f"{item['id']}: invalid attachment source page")
    if not signed or signed["type"] != "SARO" or normal(signed.get("saroNumber")) != normal(item.get("saroNumber")):
        errors.append(f"{item['id']}: invalid signed SARO link")
    if not isinstance(item.get("amountCentavos"), int) or item["amountCentavos"] < 0:
        errors.append(f"{item['id']}: invalid centavo amount")
    if item.get("itemLevel") not in {"project_or_claim", "regional_summary"}:
        errors.append(f"{item['id']}: invalid item level")
    if not item.get("description") or not (ROOT / item.get("sourcePdf", "")).is_file():
        errors.append(f"{item['id']}: missing description or one-page PDF")
    projects_by_attachment.setdefault(item["attachmentDocumentId"], []).append(item)

for entry in project_data.get("coverage", []):
    attachment = document_ids.get(entry["attachmentDocumentId"])
    attachment_items = projects_by_attachment.get(entry["attachmentDocumentId"], [])
    pages = sorted({item["sourcePage"] for item in attachment_items})
    if pages != entry["transcribedPdfPages"]:
        errors.append(f"{entry['attachmentDocumentId']}: project coverage pages differ")
    if sum(item["amountCentavos"] for item in attachment_items) != entry.get("transcribedAmountCentavos"):
        errors.append(f"{entry['attachmentDocumentId']}: project coverage amount differs")
    if entry["complete"] and (not attachment or pages != list(range(attachment["pageStart"], attachment["pageEnd"] + 1))):
        errors.append(f"{entry['attachmentDocumentId']}: incomplete attachment marked complete")
    if entry["complete"] and entry.get("reportedTotalCentavos") is not None and entry.get("differenceCentavos") != entry["reportedTotalCentavos"] - entry["transcribedAmountCentavos"]:
        errors.append(f"{entry['attachmentDocumentId']}: reconciliation difference differs")
    if entry["complete"] and entry.get("signedOrderTotalCentavos") is not None and entry.get("signedOrderDifferenceCentavos") != entry["signedOrderTotalCentavos"] - entry["transcribedAmountCentavos"]:
        errors.append(f"{entry['attachmentDocumentId']}: signed-order difference differs")

for row in saros:
    code = row["sourceAnnex"]
    source = source_codes.get(code)
    if not source or not 1 <= row["sourcePage"] <= source["pages"]:
        errors.append(f"{row['id']}: invalid purpose-list source/page")
    if row["fiscalYear"] != {"A": 2024, "D": 2025, "G": 2026}.get(code):
        errors.append(f"{row['id']}: fiscal year/source mismatch")
    order_id = row.get("orderDocumentId")
    if order_id:
        order = document_ids.get(order_id)
        if not order or order["type"] != "SARO" or normal(order.get("saroNumber")) != normal(row.get("saroNumber")):
            errors.append(f"{row['id']}: invalid exact-number order link")
        elif row.get("amountPesos") != order.get("amountPesos"):
            errors.append(f"{row['id']}: amount differs from linked order")
    elif row.get("amountPesos") is not None:
        errors.append(f"{row['id']}: amount without linked order")
    for related in row.get("relatedDocumentIds", []):
        if related not in document_ids:
            errors.append(f"{row['id']}: unknown related document {related}")

purpose_ids = {row["id"]: row for row in saros}
for row in listings:
    source = source_codes.get(row["sourceAnnex"])
    if not source or not 1 <= row["sourcePage"] <= source["pages"]:
        errors.append(f"{row['id']}: invalid listing source page")
    expected_range = {("C", "10508463"): (136, 270), ("C", "10508462"): (271, 798), ("F", "10508462"): (35, 176)}.get((row["sourceAnnex"], row["fundingSourceCode"]))
    if not expected_range or not expected_range[0] <= row["sourcePage"] <= expected_range[1] or row["printedPage"] != row["sourcePage"] - expected_range[0] + 1:
        errors.append(f"{row['id']}: listing section or printed page differs")
    if row["fiscalYear"] != {"C": 2024, "F": 2025}.get(row["sourceAnnex"]):
        errors.append(f"{row['id']}: listing fiscal year differs")
    if not (ROOT / row["sourcePdf"]).is_file():
        errors.append(f"{row['id']}: missing one-page listing PDF")
    amounts = [row.get(key) for key in ("psCentavos", "mooeCentavos", "finexCentavos", "coCentavos", "totalCentavos")]
    if any(not isinstance(value, int) for value in amounts) or sum(amounts[:4]) != amounts[4]:
        errors.append(f"{row['id']}: listing amount columns differ")
    if any(value < 0 for value in amounts) and not any(term in (row.get("reviewNote") or "").lower() for term in ("negative", "parenthesized")):
        errors.append(f"{row['id']}: signed adjustment lacks source note")
    purpose = purpose_ids.get(row.get("purposeListId"))
    if row.get("purposeListId") and (not purpose or normal(purpose.get("saroNumber")) != normal(row.get("saroNumber"))):
        errors.append(f"{row['id']}: invalid purpose-list link")
    signed = document_ids.get(row.get("signedDocumentId"))
    if row.get("signedDocumentId") and (not signed or signed["type"] != "SARO" or normal(signed.get("saroNumber")) != normal(row.get("saroNumber"))):
        errors.append(f"{row['id']}: invalid signed-document link")
for entry in listing_data.get("coverage", []):
    subset = [row for row in listings if (row["sourceAnnex"], row["fundingSourceCode"]) == (entry["sourceAnnex"], entry["fundingSourceCode"])]
    if sorted({row["sourcePage"] for row in subset}) != entry["transcribedPdfPages"] or len(subset) != entry["transactionCount"] or sum(row["totalCentavos"] for row in subset) != entry["transcribedTotalCentavos"]:
        errors.append(f"{entry['sourceAnnex']}/{entry['fundingSourceCode']}: listing coverage differs")
    if entry.get("allPagesRepresented") and not entry["complete"]:
        documented_ten_peso_difference = (
            (entry["sourceAnnex"], entry["fundingSourceCode"]) == ("C", "10508462")
            and entry["transactionCount"] == entry["reportedTransactionCount"] == 4166
            and entry["transcribedTotalCentavos"] - entry["reportedTotalCentavos"] == -1000
            and entry.get("reconciliation", {}).get("rowMinusPrintedCentavos") == -1000
            and (DATA / entry.get("reconciliation", {}).get("note", "")).is_file()
        )
        if not documented_ten_peso_difference:
            errors.append(
                f"{entry['sourceAnnex']}/{entry['fundingSourceCode']}: all pages represented but listing total unresolved "
                f"({entry['transactionCount'] - entry['reportedTransactionCount']:+d} rows, "
                f"{entry['transcribedTotalCentavos'] - entry['reportedTotalCentavos']:+d} centavos)"
            )
    if entry["complete"] and (entry["transactionCount"] != entry["reportedTransactionCount"] or entry["transcribedTotalCentavos"] != entry["reportedTotalCentavos"]):
        errors.append(f"{entry['sourceAnnex']}/{entry['fundingSourceCode']}: complete listing does not reconcile")
for row in advice_items:
    if row["sourceAnnex"] != "B" or (row["sourcePage"], row["amountStage"]) not in {(95, "requested"), (96, "variance"), (105, "requested")}:
        errors.append(f"{row['id']}: invalid advice source or stage")
    if not (ROOT / row["sourcePdf"]).is_file():
        errors.append(f"{row['id']}: missing one-page advice PDF")
    if not isinstance(row.get("amountCentavos"), int) or row["amountCentavos"] < 0:
        errors.append(f"{row['id']}: invalid advice amount")
    if row["isDuplicate"] and (row["includeInStageTotal"] or not row.get("duplicateOf")):
        errors.append(f"{row['id']}: repeated advice row would be double counted")
    if row["sourcePage"] == 105 and row.get("parentLineNumber"):
        parent = next((item for item in advice_items if item["sourcePage"] == 105 and item["lineNumber"] == row["parentLineNumber"]), None)
        if not parent or row["includeInStageTotal"]:
            errors.append(f"{row['id']}: nested advice detail is unlinked or double counted")
    if not row.get("description"):
        errors.append(f"{row['id']}: missing advice description")
for entry in advice_data.get("coverage", []):
    subset = [row for row in advice_items if row["amountStage"] == entry["amountStage"] and row["sourcePage"] == entry["sourcePage"]]
    included = [row for row in subset if row["includeInStageTotal"]]
    if sorted({row["sourcePage"] for row in subset}) != entry["sourcePages"] or len(subset) != entry["recordCount"] or len(included) != entry["includedRecordCount"] or sum(row["amountCentavos"] for row in included) != entry["transcribedTotalCentavos"] or entry["transcribedTotalCentavos"] != entry["printedTotalCentavos"]:
        errors.append(f"Advice {entry['amountStage']}: coverage or printed total differs")
road_schedules = {1: (2, 57, 2024, "current"), 2: (58, 73, 2024, "continuing"), 3: (74, 115, 2025, "current"), 4: (116, 159, 2025, "continuing")}
road_keys = Counter((row["sourcePage"], row["lineNumber"]) for row in road_projects)
for (page, line), count in road_keys.items():
    if count != 1:
        errors.append(f"Annex L page {page} line {line}: duplicate")
for row in road_projects:
    schedule = road_schedules.get(row["scheduleNumber"])
    if not schedule or not schedule[0] <= row["sourcePage"] <= schedule[1] or row["fiscalYear"] != schedule[2] or row["appropriationType"] != schedule[3]:
        errors.append(f"{row['id']}: wrong Annex L schedule/page/year")
    if schedule and row["printedPage"] != row["sourcePage"] - schedule[0] + 1:
        errors.append(f"{row['id']}: wrong printed page")
    if row["sourceAnnex"] != "L" or not (ROOT / row["sourcePdf"]).is_file():
        errors.append(f"{row['id']}: missing or invalid one-page source PDF")
    if not row.get("description"):
        errors.append(f"{row['id']}: missing project description")
    amount_keys = ("authorizedAppropriationCentavos", "beginningBalanceCentavos", "gaaaoCentavos", "fisaroCentavos", "totalAllotmentsCentavos", "obligationsCentavos", "disbursementsCentavos", "unobligatedBalanceCentavos", "unpaidObligationsCentavos")
    if any(value is not None and (not isinstance(value, int) or value < 0) for value in (row.get(key) for key in amount_keys)):
        errors.append(f"{row['id']}: invalid amount")
    gaaao = row.get("gaaaoCentavos") or 0
    obligations = row.get("obligationsCentavos") or 0
    disbursements = row.get("disbursementsCentavos") or 0
    allotments = row.get("totalAllotmentsCentavos")
    if row["scheduleNumber"] == 3:
        if allotments is None or gaaao + (row.get("fisaroCentavos") or 0) != allotments:
            errors.append(f"{row['id']}: GAAAO and FISARO do not equal total allotments")
    if row["scheduleNumber"] == 3:
        balance_base = allotments
    elif row["scheduleNumber"] == 4:
        if row.get("beginningBalanceCentavos") is None and any(
            row.get(field) is not None for field in (
                "obligationsCentavos", "disbursementsCentavos",
                "unobligatedBalanceCentavos", "unpaidObligationsCentavos",
            )
        ):
            errors.append(f"{row['id']}: missing continuing-appropriation beginning balance")
        balance_base = row.get("beginningBalanceCentavos") or 0
    else:
        balance_base = gaaao
    appropriation_difference = balance_base - obligations - (row.get("unobligatedBalanceCentavos") or 0)
    if appropriation_difference:
        errors.append(f"{row['id']}: appropriation balance differs from allotment less obligations")
    unpaid = row.get("unpaidObligationsCentavos") or 0
    # These are visible printed arithmetic differences, retained verbatim in
    # the transcription and flagged in each affected row's review note.
    printed_differences = {
        "road-l-p022-005": -18000,
        "road-l-p024-017": 18000000,
    }
    if obligations - disbursements - unpaid != printed_differences.get(row["id"], 0):
        errors.append(f"{row['id']}: unpaid balance differs from checked printed variance")
    if row["id"] in printed_differences and not row.get("reviewNote"):
        errors.append(f"{row['id']}: printed arithmetic difference lacks review note")
for entry in road_data.get("coverage", []):
    schedule = road_schedules[entry["scheduleNumber"]]
    subset = [row for row in road_projects if row["scheduleNumber"] == entry["scheduleNumber"]]
    pages = sorted({row["sourcePage"] for row in subset})
    if pages != entry["transcribedPdfPages"] or len(subset) != entry["recordCount"]:
        errors.append(f"Annex L schedule {entry['scheduleNumber']}: coverage differs")
    if entry["scheduleNumber"] == 2 and entry["complete"]:
        printed_totals = {
            "authorizedAppropriationCentavos": 78169414417,
            "obligationsCentavos": 76650557627,
            "disbursementsCentavos": 38896551346,
            "unobligatedBalanceCentavos": 1518856790,
            "unpaidObligationsCentavos": 37754006281,
        }
        if len(subset) != 325 or any(sum(row.get(field) or 0 for row in subset) != expected for field, expected in printed_totals.items()):
            errors.append("Annex L schedule 2: complete project rows differ from printed totals")
    if entry["scheduleNumber"] == 3 and entry["complete"]:
        printed_totals = {
            "authorizedAppropriationCentavos": 3474802000000,
            "gaaaoCentavos": 754551000000,
            "fisaroCentavos": 2720251000000,
            "totalAllotmentsCentavos": 3474802000000,
            "obligationsCentavos": 2960368575553,
            "disbursementsCentavos": 1293400685886,
            "unobligatedBalanceCentavos": 514433424447,
            "unpaidObligationsCentavos": 1666967889667,
        }
        # The visually transcribed rows have three exact, unresolved differences
        # from the repeated printed header; retain both figures for review.
        known_differences = {
            "gaaaoCentavos": 2330200000,
            "fisaroCentavos": -2330200000,
            "obligationsCentavos": 5000,
            "unobligatedBalanceCentavos": -5000,
            "unpaidObligationsCentavos": 5000,
        }
        if len(subset) != 824 or any(
            sum(row.get(field) or 0 for row in subset) - expected != known_differences.get(field, 0)
            for field, expected in printed_totals.items()
        ):
            errors.append("Annex L schedule 3: complete project rows differ from documented reconciliation")
    if entry["scheduleNumber"] == 4 and entry["complete"]:
        printed_totals = {
            "beginningBalanceCentavos": 75577129961,
            "obligationsCentavos": 47778533248,
            "disbursementsCentavos": 22198354609,
            "unobligatedBalanceCentavos": 27798596713,
            "unpaidObligationsCentavos": 25580178639,
        }
        if len(subset) != 730 or any(
            sum(row.get(field) or 0 for row in subset) != expected
            for field, expected in printed_totals.items()
        ):
            errors.append("Annex L schedule 4: complete project rows differ from printed totals")
    if entry["complete"] != (pages == list(range(schedule[0], schedule[1] + 1))):
        errors.append(f"Annex L schedule {entry['scheduleNumber']}: complete flag differs")
for row in status_rows:
    source = source_codes.get(row["sourceAnnex"])
    pages = row.get("sourcePages") or []
    if not source or not pages or any(not 1 <= page <= source["pages"] for page in pages):
        errors.append(f"{row['id']}: invalid status source pages")
    if len(row.get("sourcePagePdfs") or []) != len(pages):
        errors.append(f"{row['id']}: missing one-page PDF links")
    for pdf in row.get("sourcePagePdfs") or []:
        if not (ROOT / pdf).is_file():
            errors.append(f"{row['id']}: missing source PDF {pdf}")
    linked = row.get("purposeListId")
    if linked:
        purpose = purpose_ids.get(linked)
        if not purpose or purpose["fiscalYear"] != row["fiscalYear"] or normal(purpose.get("saroNumber")) != normal(row.get("saroNumber")):
            errors.append(f"{row['id']}: invalid purpose-list link")

for row in agency_expenditure:
    if row["sourceAnnex"] != "M" or not 1 <= row["sourcePage"] <= 20 or not (ROOT / row["sourcePdf"]).is_file():
        errors.append(f"{row['id']}: invalid Annex M page source")
    if row["unit"] != "thousand pesos" or row["year"] not in {2024, 2025, 2026} or not row["hierarchyPath"]:
        errors.append(f"{row['id']}: invalid Annex M dimensions")
    difference = sum(row[field] for field in (
        "personnelServices", "maintenanceAndOtherOperatingExpenses", "capitalOutlaysAndNetLending", "financialExpenses"
    )) - row["total"]
    if difference and not row.get("reviewNote"):
        errors.append(f"{row['id']}: printed amount variance lacks note")
    if row["includeInGrandTotal"] != (row["rowType"] == "detail"):
        errors.append(f"{row['id']}: agency grand-total inclusion differs from row type")
    if row["rowType"] == "repeated" and not row.get("reviewNote"):
        errors.append(f"{row['id']}: repeated source row lacks note")
for row in road_summary:
    if row["sourceAnnex"] != "L" or row["sourcePage"] != 1 or not (ROOT / row["sourcePdf"]).is_file():
        errors.append(f"{row['id']}: invalid Road Fund summary source")
    allotments = row["allotmentsCentavos"]
    obligations = row["obligationsCentavos"]
    disbursements = row["disbursementsCentavos"]
    if allotments - obligations != row["unobligatedAllotmentsCentavos"] or obligations - disbursements != row["unpaidObligationsCentavos"]:
        errors.append(f"{row['id']}: Road Fund summary balance differs")
for row in process_steps:
    if row["sourceAnnex"] != "K" or not 1 <= row["sourcePage"] <= 3 or not (ROOT / row["sourcePdf"]).is_file():
        errors.append(f"{row['id']}: invalid Annex K process source")
    if not row["section"] or not row["entryType"] or not (row["text"] or row["items"]):
        errors.append(f"{row['id']}: empty process entry")
for row in debt_reference:
    source = source_codes.get(row["sourceAnnex"])
    if not source or row["sourceAnnex"] not in {"N", "O", "P"} or not 1 <= row["sourcePage"] <= source["pages"] or not (ROOT / row["sourcePdf"]).is_file():
        errors.append(f"{row['id']}: invalid debt source")
    precision = 1_000_000 if row["printedUnit"] == "million pesos" else 1 if row["printedUnit"] == "pesos" else None
    if precision is None or row["precisionPesos"] != precision or row["amountPesos"] != row["printedAmount"] * precision:
        errors.append(f"{row['id']}: debt unit conversion differs")
    if row["sourceAnnex"] == "P":
        difference = row["domesticPrintedAmount"] + row["foreignPrintedAmount"] - row["printedAmount"]
        if abs(difference) > 1 or (difference and not row.get("reviewNote")):
            errors.append(f"{row['id']}: domestic/foreign split differs from printed total")
o_rows = [row for row in debt_reference if row["sourceAnnex"] == "O"]
if len(o_rows) != 1338 or {row["year"] for row in o_rows} != set(range(1986, 2026)):
    errors.append("Annex O historical instrument/year rows incomplete")
if any(not any(row["year"] == year and row["rowType"] == "grandTotal" for row in o_rows) for year in range(1986, 2026)):
    errors.append("Annex O historical grand-total row missing for a year")
if not (DATA / debt_data.get("reconciliationNote", "")).is_file():
    errors.append("Debt-reference reconciliation note missing")
if len(agency_data.get("transcribedPdfPages", [])) == 20:
    known_differences = {
        2024: {"personnelServices": 0, "maintenanceAndOtherOperatingExpenses": 0, "capitalOutlaysAndNetLending": 0, "financialExpenses": 0, "total": 0},
        2025: {"personnelServices": 0, "maintenanceAndOtherOperatingExpenses": 18000, "capitalOutlaysAndNetLending": 0, "financialExpenses": 0, "total": 0},
        2026: {"personnelServices": 0, "maintenanceAndOtherOperatingExpenses": 0, "capitalOutlaysAndNetLending": 0, "financialExpenses": 0, "total": 0},
    }
    if {entry["year"]: entry["detailMinusPrintedThousandPesos"] for entry in agency_data.get("reconciliation", [])} != known_differences:
        errors.append("Annex M detail sums differ from documented printed-grand-total reconciliation")
    if not (DATA / agency_data.get("reconciliationNote", "")).is_file():
        errors.append("Annex M reconciliation note missing")

for cell in status_allocations:
    parent = status_ids.get(cell["statusRowId"])
    if not parent:
        errors.append(f"{cell['id']}: missing status row")
        continue
    if cell["sourceAnnex"] != parent["sourceAnnex"] or cell["sourcePage"] not in parent["sourcePages"]:
        errors.append(f"{cell['id']}: source page outside row span")
    if cell["saroNumber"] != parent["saroNumber"] or cell.get("purposeListId") != parent.get("purposeListId"):
        errors.append(f"{cell['id']}: status link differs from parent")
    if not isinstance(cell.get("amountPesos"), int):
        errors.append(f"{cell['id']}: allocation is not integer pesos")
    if not cell.get("category") or not cell.get("expenseClass"):
        errors.append(f"{cell['id']}: missing category or expense class")
    if not (ROOT / cell.get("standalonePdf", "")).is_file():
        errors.append(f"{cell['id']}: missing one-page source PDF")

with (DATA / "status_rollups.csv").open(encoding="utf-8-sig", newline="") as stream:
    rollup_csv_ids = [row["id"] for row in csv.DictReader(stream)]
if rollup_csv_ids != [row["id"] for row in status_rollups]:
    errors.append("Status-rollup CSV differs from JSON")
for cell in status_rollups:
    source = source_codes.get(cell["sourceAnnex"])
    if not source or not 1 <= cell["sourcePage"] <= source["pages"] or not (ROOT / cell["sourcePdf"]).is_file():
        errors.append(f"{cell['id']}: invalid status-rollup source")
    precision = 1000 if cell["printedUnit"] == "thousand pesos" else 1 if cell["printedUnit"] == "pesos" else None
    if precision is None or cell["precisionPesos"] != precision or cell["amountPesos"] != cell["printedAmount"] * precision:
        errors.append(f"{cell['id']}: inconsistent printed unit conversion")
for note in status_notes:
    source = source_codes.get(note["sourceAnnex"])
    if not source or not 1 <= note["sourcePage"] <= source["pages"] or not (ROOT / note["sourcePdf"]).is_file():
        errors.append(f"{note['id']}: invalid status-note source")
    if not note.get("textAsTranscribed"):
        errors.append(f"{note['id']}: empty status note")

department_names: dict[str, str] = {}
for row in saros:
    code = row.get("departmentCode")
    name = row.get("department")
    if code and not name:
        errors.append(f"{row['id']}: department code without name")
    if code in department_names and department_names[code] != name:
        errors.append(f"{row['id']}: inconsistent department name for {code}")
    if code:
        department_names[code] = name

for row in schemas:
    if row["status"] not in {"planned", "partial", "published"}:
        errors.append(f"{row['id']}: unexpected schema status")
    for code in row["annexIds"]:
        if code not in source_codes:
            errors.append(f"{row['id']}: unknown source Annex {code}")

print(f"{len(saros)} SARO list entries, {len(documents)} documents, {len(sources)} sources, {len(schemas)} dataset schemas")
print(f"Signed SARO links: {sum(bool(row.get('orderDocumentId')) for row in saros)}")
print(f"Particular lines: {len(particulars)} across {len(lines_by_document)} signed SAROs")
print(f"Attachment project lines: {len(projects)} across {len(projects_by_attachment)} attachments")
print(f"eBudget transactions: {len(listings)} across {len({(row['sourceAnnex'], row['sourcePage']) for row in listings})} source pages")
print(f"Advice request/variance rows: {len(advice_items)} across {len({row['sourcePage'] for row in advice_items})} source pages")
print(f"Advice document component cells: {len(document_components)} across {len({(row['sourceAnnex'], row['sourcePage']) for row in document_components})} source pages")
print(f"Road-fund projects: {len(road_projects)} across {len({row['sourcePage'] for row in road_projects})} source pages")
print(f"Road-fund summary: {len(road_summary)} rows; release process: {len(process_steps)} entries")
print(f"Agency expenditure: {len(agency_expenditure)} row-year records across {len({row['sourcePage'] for row in agency_expenditure})} source pages")
print(f"Debt reference: {len(debt_reference)} rows across {len({(row['sourceAnnex'], row['sourcePage']) for row in debt_reference})} source pages")
print(f"Revenue evidence: {len(revenue_documents)} documents and {len(revenue_csv)} amount rows across {len({row['sourcePage'] for row in revenue_documents})} source pages")
print(f"Revenue release-status cells: {len(revenue_status)} across {len({row['sourcePage'] for row in revenue_status})} source pages")
print(f"Status rows: {len(status_rows)}; allocation cells: {len(status_allocations)}; summary cells: {len(status_rollups)}; report notes: {len(status_notes)}")
print(f"Documented source discrepancies and evidence limits: {len(discrepancies)}")
print(f"Issues: {len(errors)}")
for error in errors:
    print(f"- {error}")
raise SystemExit(bool(errors))
