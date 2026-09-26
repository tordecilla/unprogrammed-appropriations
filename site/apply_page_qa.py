"""Apply independent image-based page/number corrections to Annex B segments."""

from __future__ import annotations

import json
from pathlib import Path


DATA = Path(__file__).parent / "data"
segment_path = DATA / "segments_b_early.json"
segments = json.loads(segment_path.read_text(encoding="utf-8-sig"))
checks = json.loads((DATA / "qa_b_index.json").read_text(encoding="utf-8-sig"))
by_page = {row["pageStart"]: row for row in segments}

for check in checks:
    segment = by_page[check["pageStart"]]
    if segment["saroNumber"] != check["recordedNumber"]:
        raise ValueError(f"Source segment changed after QA: page {check['pageStart']}")
    if segment["pageEnd"] != check["actualPageEnd"]:
        raise ValueError(f"Source span changed after QA: page {check['pageStart']}")
    segment["saroNumber"] = check["actualNumber"]
    segment["confidence"] = check["confidence"]
    segment["note"] = check["note"]

segment_path.write_text(json.dumps(segments, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Applied {len(checks)} independently reviewed page/number corrections")
