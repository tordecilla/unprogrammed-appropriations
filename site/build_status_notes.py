"""Publish visually transcribed report-level notes separately from money rows."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


DATA = Path(__file__).parent / "data"
INPUTS = ("status_c_100_105_report_notes.json",)
ordinals = Counter()
rows = []
for filename in INPUTS:
    staged = json.loads((DATA / filename).read_text(encoding="utf-8-sig"))
    for source in staged["records"]:
        code = source["annexId"].upper()
        page = source["sourcePage"]
        ordinals[(code, page)] += 1
        rows.append({
            "id": f"{code.lower()}-status-note-p{page:03d}-{ordinals[(code, page)]:02d}",
            "sourceAnnex": code,
            "sourcePage": page,
            "printedPage": source["printedPage"],
            "sourcePdf": f"status-pages/annex-{code.lower()}-p{page:03d}.pdf",
            "type": source["type"],
            "scope": source["scope"],
            "textAsTranscribed": source["noteText"],
            "reviewNote": source.get("reviewNote"),
        })
(DATA / "status_report_notes.json").write_text(
    json.dumps({"version": 1, "grain": "one status-report provenance note", "records": rows}, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)
print(f"Built {len(rows)} status-report notes")
