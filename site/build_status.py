"""Build linked UA status rows from visual page transcriptions.

Input JSON is read from page-image transcriptions. No PDF extraction is used.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path


DATA = Path(__file__).parent / "data"
INPUTS = ("status_c_4_20.json", "status_c_9_20.json", "status_c_16_19.json", "status_c_21_37.json", "status_c_32_55.json", "status_c_36_next.json", "status_c_40_45.json", "status_c_48_55.json", "status_c_56_63.json", "status_c_64_71.json", "status_c_72_79.json", "status_c_80_87.json", "status_c_88_95.json", "status_c_96_99.json", "status_c_100_105.json", "status_c_106_111.json", "status_c_112_119.json", "status_c_120_127.json", "status_c_128_135.json", "status_f_2_18.json", "status_f_7_gap.json", "status_f_8_34.json", "status_f_11_14.json", "status_f_17_20.json", "status_f_21_24.json", "status_f_29_34.json")
DEPARTMENTS = {
    "DA": "Department of Agriculture",
    "DAR": "Department of Agrarian Reform",
    "DENR": "Department of Environment and Natural Resources",
    "DFA": "Department of Foreign Affairs",
    "DOE": "Department of Energy",
    "DOF": "Department of Finance",
    "OP": "Office of the President",
    "OVP": "Office of the Vice President",
    "SUCs": "State Universities and Colleges",
}


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def normal(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def iso_date(value: str | None) -> str | None:
    if not value:
        return None
    for pattern in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(value.strip(), pattern).date().isoformat()
        except ValueError:
            pass
    return None


saros = read("saros.json")["records"]
documents = read("documents.json")["records"]
by_year_number: dict[tuple[int, str], list[dict]] = {}
for record in saros:
    if record.get("saroNumber"):
        by_year_number.setdefault((record["fiscalYear"], normal(record["saroNumber"])), []).append(record)
documents_by_number: dict[str, list[dict]] = {}
for document in documents:
    if document.get("type") == "SARO" and document.get("saroNumber"):
        documents_by_number.setdefault(normal(document["saroNumber"]), []).append(document)
department_codes = {record["department"]: record["departmentCode"] for record in saros if record.get("departmentCode") and record.get("department")}
department_codes.update({name: code for code, name in DEPARTMENTS.items()})

status_rows = []
allocations = []
for filename in INPUTS:
    if not (DATA / filename).exists():
        continue
    for ordinal, source in enumerate(read(filename), start=1):
        code = source["annexId"].upper()
        year = {"C": 2024, "F": 2025}[code]
        first_page = int(source["pdfPage"])
        record_id = f"{code.lower()}-status-p{first_page:03d}-r{ordinal:03d}"
        matches = by_year_number.get((year, normal(source.get("saroNumber"))), [])
        document_matches = documents_by_number.get(normal(source.get("saroNumber")), [])
        source_pages = sorted(set(int(page) for page in (source.get("sourcePages") or [first_page])))
        department_raw = source.get("department")
        department = DEPARTMENTS.get(department_raw, department_raw)
        if len(matches) == 1:
            department = matches[0].get("department") or department
        agency = (matches[0].get("agency") if len(matches) == 1 else None) or source.get("agency")
        row = {
            "id": record_id,
            "fiscalYear": year,
            "sourceAnnex": code,
            "sourcePages": source_pages,
            "printedPage": source.get("printedPage"),
            "saroNumber": source.get("saroNumber"),
            "sourceDateLabel": source.get("date"),
            "date": iso_date(source.get("date")),
            "departmentRaw": department_raw,
            "departmentCode": matches[0].get("departmentCode") if len(matches) == 1 else department_codes.get(department),
            "department": department,
            "agency": agency,
            "purpose": source.get("purpose"),
            "reportedTotalPesos": source.get("reportedTotalPesos"),
            "reviewNote": source.get("reviewNote"),
        }
        if len(matches) == 1:
            row["purposeListId"] = matches[0]["id"]
        elif len(matches) > 1:
            row["candidatePurposeListIds"] = [match["id"] for match in matches]
        if len(document_matches) == 1:
            row["signedDocumentId"] = document_matches[0]["id"]
        status_rows.append(row)
        for index, cell in enumerate(source.get("allocations") or [], start=1):
            amount = cell.get("amountPesos")
            if amount is None:
                continue
            allocations.append({
                "id": f"{record_id}-a{index:02d}",
                "statusRowId": record_id,
                "fiscalYear": year,
                "sourceAnnex": code,
                "sourcePage": int(cell.get("pdfPage") or first_page),
                "saroNumber": row["saroNumber"],
                "purposeListId": row.get("purposeListId"),
                "category": cell.get("category"),
                "expenseClass": cell.get("expenseClass"),
                "amountPesos": amount,
            })

(DATA / "status_rows.json").write_text(json.dumps({"version": 1, "grain": "one numbered SARO row in a UA status report", "records": status_rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(DATA / "status_allocations.json").write_text(json.dumps({"version": 1, "grain": "one expense-class allocation cell in a UA status report", "records": allocations}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Built {len(status_rows)} status rows and {len(allocations)} allocation cells; {sum('purposeListId' in row for row in status_rows)} exact purpose-list links")
