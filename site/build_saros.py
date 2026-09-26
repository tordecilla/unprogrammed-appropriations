"""Build one public record per visually transcribed SARO purpose-list entry."""

from __future__ import annotations

import json
import re
from pathlib import Path


DATA = Path(__file__).parent / "data"


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def normal_number(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def split_agency(label: str | None) -> tuple[str | None, str | None, str | None]:
    if not label:
        return None, None, None
    if label == "General Headquarters - Proper":
        return None, label, None
    parts = [part.strip() for part in re.split(r"\s+[-\u2013\u2014]\s+", label) if part.strip()]
    if len(parts) == 1:
        return None, parts[0], None
    return parts[0], parts[-1], " / ".join(parts[1:-1]) or None


DEPARTMENTS = {
    "DAR": ("DAR", "Department of Agrarian Reform"),
    "DEPARTMENT OF AGRARIAN REFORM": ("DAR", "Department of Agrarian Reform"),
    "DA": ("DA", "Department of Agriculture"),
    "DOH": ("DOH", "Department of Health"),
    "DEPARTMENT OF HEALTH": ("DOH", "Department of Health"),
    "DOTr": ("DOTr", "Department of Transportation"),
    "DEPARTMENT OF TRANSPORTATION": ("DOTr", "Department of Transportation"),
    "DPWH": ("DPWH", "Department of Public Works and Highways"),
    "DEPARTMENT OF PUBLIC WORKS": ("DPWH", "Department of Public Works and Highways"),
    "DSWD": ("DSWD", "Department of Social Welfare and Development"),
    "DEPARTMENT OF SOCIAL WELFARE AND DEVELOPMENT": ("DSWD", "Department of Social Welfare and Development"),
    "DepEd": ("DepEd", "Department of Education"),
    "DEPARTMENT OF EDUCATION": ("DepEd", "Department of Education"),
    "DTI": ("DTI", "Department of Trade and Industry"),
    "DEPARTMENT OF FINANCE": ("DOF", "Department of Finance"),
    "DEPARTMENT OF INFORMATION AND COMMUNICATION": ("DICT", "Department of Information and Communications Technology"),
    "DEPARTMENT OF JUSTICE": ("DOJ", "Department of Justice"),
    "DEPARTMENT OF NATIONAL DEFENSE": ("DND", "Department of National Defense"),
    "NEDA": ("NEDA", "National Economic and Development Authority"),
    "DEPARTMENT OF ECONOMY, PLANNING AND DEVELOPMENT (formerly NEDA)": ("DEPDev", "Department of Economy, Planning and Development"),
    "OEO": ("OEO", "Other Executive Offices"),
    "OTHER EXECUTIVE OFFICES": ("OEO", "Other Executive Offices"),
    "Special Purpose Funds": ("SPF", "Special Purpose Funds"),
    "SPECIAL PURPOSE FUND": ("SPF", "Special Purpose Funds"),
    "ALGU": ("SPF", "Special Purpose Funds"),
}

AGENCIES = {
    "ALGU": "Local Government Units",
    "LGUs": "Local Government Units",
    "CIVIL SERVICE COMMISSION": "Civil Service Commission",
    "Bureau of Local Government Finances": "Bureau of Local Government Finance",
}


list_rows = []
for filename in ("releases_a_1_3.json", "releases_a_4_6.json", "releases_dg.json"):
    list_rows.extend(read(filename))
documents = read("documents.json")["records"]
orders_by_number = {}
for document in documents:
    if document["type"] == "SARO" and document.get("saroNumber") and document.get("numberMatchEligible", True):
        orders_by_number.setdefault(normal_number(document["saroNumber"]), []).append(document)

records = []
seen_ids = set()
for row in list_rows:
    code = row["annexId"].upper()
    number = row.get("listNumber")
    if number is None:
        serial = sum(item["sourceAnnex"] == code and item.get("listNumber") is None for item in records) + 1
        record_id = f"{code.lower()}-p{row['pdfPage']}-unnumbered-{serial}"
    else:
        record_id = f"{code.lower()}-{int(number):03}"
    if record_id in seen_ids:
        raise ValueError(f"Duplicate purpose-list row: {record_id}")
    seen_ids.add(record_id)
    year = {"A": 2024, "D": 2025, "G": 2026}[code]
    source_department, source_agency, agency_group = split_agency(row.get("agency") or row.get("agencyContext"))
    if source_department and source_department not in DEPARTMENTS:
        raise ValueError(f"Unmapped department label: {source_department}")
    department_code, department = DEPARTMENTS.get(source_department, (None, None))
    agency = AGENCIES.get(source_agency, source_agency)
    record = {
        "id": record_id,
        "fiscalYear": year,
        "sourceAnnex": code,
        "sourcePage": row["pdfPage"],
        "listNumber": number,
        "saroNumber": row.get("saroNumber"),
        "date": row.get("date"),
        "department": department,
        "departmentCode": department_code,
        "agency": agency,
        "agencyGroup": agency_group,
        "sourceDepartmentLabel": source_department,
        "sourceAgencyName": source_agency,
        "sourceAgencyLabel": row.get("agency"),
        "agencyContextSourcePage": row.get("agencyContextSourcePage"),
        "purpose": row.get("purpose"),
        "remarks": row.get("remarks"),
        "reviewNote": row.get("reviewNote"),
    }
    matches = orders_by_number.get(normal_number(row.get("saroNumber")), [])
    if len(matches) == 1:
        order = matches[0]
        record["orderDocumentId"] = order["id"]
        if order.get("amountPesos") is not None:
            record["amountPesos"] = order["amountPesos"]
            record["amountStage"] = order.get("amountStage")
        record["relatedDocumentIds"] = order.get("relatedIds", [])
    elif len(matches) > 1:
        record["candidateOrderDocumentIds"] = [item["id"] for item in matches]
    records.append(record)

records.sort(key=lambda row: (row["fiscalYear"], row["sourceAnnex"], row["sourcePage"], row["listNumber"] if row["listNumber"] is not None else 100000, row["id"]))
output = {"version": 1, "grain": "one SARO purpose-list entry", "records": records}
(DATA / "saros.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"{len(records)} list entries; {sum('orderDocumentId' in row for row in records)} exact-number order links")
