"""Merge visually bounded Annex B advice documents into the source registry."""

from __future__ import annotations

import json
from pathlib import Path


DATA = Path(__file__).parent / "data"
CATALOG = DATA / "documents.json"
STAGING = (
    DATA / "annex_b_uncovered_2_33_staging.json",
    DATA / "annex_b_uncovered_35_58_staging.json",
    DATA / "annex_b_uncovered_68_110_staging.json",
    DATA / "annex_b_uncovered_106_309_staging.json",
    DATA / "annex_b_uncovered_312_348_staging.json",
)
SOURCE = "../court-documents/Annex-B-Compliance-G.R.-No.271059.pdf"

staged = [
    row
    for path in STAGING
    for row in json.loads(path.read_text(encoding="utf-8-sig"))["records"]
]
catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
by_id = {row["id"]: row for row in catalog["records"]}
duplicates = {21: 18, 33: 25}

added = 0
for source in staged:
    first = source["pageStart"]
    if not source["type"].startswith("Advice of SARO"):
        # Context forms are already indexed as their signed SARO documents.
        continue
    last = source["pageEnd"]
    document_id = f"B-p{first:03d}" + (f"-{last:03d}" if last != first else "") + "-advice"
    if document_id in by_id:
        continue
    if any(row["annexId"] == "B" and row["pageStart"] <= first <= row["pageEnd"] for row in catalog["records"]):
        raise ValueError(f"Annex B page {first} is already indexed")
    row = {key: value for key, value in source.items() if key not in {"id", "reviewNotes"}}
    row["id"] = document_id
    row["source"] = f"{SOURCE}#page={first}"
    numbers = source.get("relatedSaroNumbers") or ([source["saroNumber"]] if source.get("saroNumber") else [])
    related_ids = [
        item["id"] for item in catalog["records"]
        if item["annexId"] == "B" and item["type"] == "SARO"
        and item.get("saroNumber") in numbers
    ]
    if len(related_ids) != len(numbers):
        raise ValueError(f"Cannot match all printed SARO references on Annex B page {first}")
    row["relatedIds"] = related_ids
    row["reviewNote"] = source["reviewNotes"]
    if first in duplicates:
        original = duplicates[first]
        row["duplicateOf"] = f"B-p{original:03d}" + ("-019" if original == 18 else "") + "-advice"
    catalog["records"].append(row)
    by_id[document_id] = row
    added += 1

if "B-p105-106-advice" in by_id and "B-p109-110-advice" in by_id:
    by_id["B-p109-110-advice"]["possibleDuplicateOf"] = "B-p105-106-advice"

catalog["records"].sort(key=lambda row: (row["annexId"], row["pageStart"], row["pageEnd"], row["id"]))
CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Added {added} Annex B advice documents")
