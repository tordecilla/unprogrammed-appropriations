"""Publish visually transcribed Annex K release-process entries."""

from __future__ import annotations

import json
from pathlib import Path


DATA = Path(__file__).parent / "data"
source = json.loads((DATA / "annex_k_process_p1_3.json").read_text(encoding="utf-8-sig"))
rows = []
for page in source["pages"]:
    for ordinal, entry in enumerate(page["entries"], start=1):
        rows.append({
            "id": f"process-k-p{page['sourcePage']:03d}-r{ordinal:02d}",
            "sourceAnnex": "K",
            "sourcePage": page["sourcePage"],
            "printedPage": page["printedPage"],
            "sourcePdf": f"process-pages/annex-k-p{page['sourcePage']:03d}.pdf",
            "section": entry["section"],
            "entryType": entry["entryType"],
            "group": entry.get("group"),
            "text": entry.get("text"),
            "items": entry.get("items", []),
        })
(DATA / "process_steps.json").write_text(json.dumps({"version": 1, "grain": "one Annex K process step, criterion, or required-document group", "records": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Built {len(rows)} Annex K process entries")
