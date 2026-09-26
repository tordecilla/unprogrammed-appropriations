"""Add visually reviewed SARO boundaries to the document catalog.

Only high-confidence visually bounded forms are ingested. An exact purpose-list
number match enriches a form, but unmatched forms remain indexed separately.
This does not inspect PDF text or infer page boundaries.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


DATA = Path(__file__).parent / "data"


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def normal(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


catalog = read("documents.json")
sources = {row["id"].removeprefix("annex-").upper(): row for row in read("annexes.json")["records"]}
list_rows = {normal(row.get("saroNumber")): row for row in read("saros.json")["records"] if row.get("saroNumber")}
segment_files = ("segments_b_early.json", "segments_b_mid_h.json", "segments_b_late.json")
segments = [(filename, segment) for filename in segment_files if (DATA / filename).exists() for segment in read(filename)]
reviewed_ids = {f"{segment['annexId']}-p{segment['pageStart']:03d}" for _, segment in segments if segment["type"].lower() == "saro"}
before = len(catalog["records"])
catalog["records"] = [row for row in catalog["records"] if row.get("boundaryReview") != "visual, high confidence" or row["id"] in reviewed_ids]
removed = before - len(catalog["records"])
by_id = {row["id"]: row for row in catalog["records"]}
added = 0
skipped = []

for filename in segment_files:
    for source_file, segment in (item for item in segments if item[0] == filename):
        if segment["type"].lower() != "saro":
            continue
        code = segment["annexId"]
        number = normal(segment.get("saroNumber"))
        list_row = list_rows.get(number)
        identifier = f"{code}-p{segment['pageStart']:03d}"
        existing = by_id.get(identifier)
        if existing:
            if (existing["pageStart"], existing["pageEnd"]) != (segment["pageStart"], segment["pageEnd"]):
                skipped.append((filename, segment["pageStart"], "conflicting page boundary"))
            elif normal(existing.get("saroNumber")) != number:
                if existing.get("boundaryReview") != "visual, high confidence":
                    skipped.append((filename, segment["pageStart"], "conflicts with earlier curated number"))
                else:
                    existing["saroNumber"] = segment["saroNumber"]
                    existing["purposeListMatch"] = bool(list_row)
                    for field in ("date", "agency", "purpose"):
                        if list_row:
                            existing[field] = list_row.get(field)
                        else:
                            existing.pop(field, None)
                    print(f"Corrected visually transcribed number: {identifier}")
            continue
        if any(row["annexId"] == code and row["type"] == "SARO" and row["pageStart"] <= segment["pageEnd"] and row["pageEnd"] >= segment["pageStart"] for row in catalog["records"]):
            skipped.append((filename, segment["pageStart"], "overlapping SARO form"))
            continue
        source = sources[code]
        document = {
            "id": identifier,
            "annexId": code,
            "type": "SARO",
            "pageStart": segment["pageStart"],
            "pageEnd": segment["pageEnd"],
            "title": "SARO",
            "source": f"../court-documents/{source['file']}#page={segment['pageStart']}",
            "audit": f"site/data/{filename}",
            "saroNumber": segment["saroNumber"],
            "boundaryReview": f"visual, {segment['confidence']} confidence number",
            "numberMatchEligible": segment["confidence"] == "high",
            "purposeListMatch": bool(list_row) and segment["confidence"] == "high",
        }
        if list_row and segment["confidence"] == "high":
            document["date"] = list_row.get("date")
            document["agency"] = list_row.get("agency")
            document["purpose"] = list_row.get("purpose")
        catalog["records"].append(document)
        by_id[identifier] = document
        added += 1

catalog["records"].sort(key=lambda row: (row["annexId"], row["pageStart"], row["pageEnd"], row["id"]))
(DATA / "documents.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Added {added} visually bounded SARO forms; removed {removed} superseded form; skipped {len(skipped)}")
for item in skipped:
    print("-", *item)
