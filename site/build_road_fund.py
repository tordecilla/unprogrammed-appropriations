"""Publish visually transcribed Annex L Special Road Fund project rows."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


SITE = Path(__file__).parent
DATA = SITE / "data"
INPUTS = ("annex_l_schedule1_p2_3.json", "annex_l_schedule1_p4.json", "annex_l_schedule1_p5.json", "annex_l_schedule1_p6.json", "annex_l_schedule1_p7.json", "annex_l_schedule1_p8.json", "annex_l_schedule1_p9.json", "annex_l_schedule1_p10.json", "annex_l_schedule1_p11.json", "annex_l_schedule1_p12.json", "annex_l_schedule1_p13.json", "annex_l_schedule1_p14.json", "annex_l_schedule1_p15.json", "annex_l_schedule1_p16.json", "annex_l_schedule1_p17.json", "annex_l_schedule1_p18.json", "annex_l_schedule1_p19.json", "annex_l_schedule1_p20.json", "annex_l_schedule1_p21_26.json", "annex_l_schedule1_p27_32.json", "annex_l_schedule1_p33_38.json", "annex_l_schedule1_p39_44.json", "annex_l_schedule1_p45_50.json", "annex_l_schedule1_p51_57.json", "annex_l_schedule2_p58_59.json", "annex_l_schedule2_p60_61.json", "annex_l_schedule2_p62_63.json", "annex_l_schedule2_p64.json", "annex_l_schedule2_p65_66.json", "annex_l_schedule2_p67_68.json", "annex_l_schedule2_p69_70.json", "annex_l_schedule2_p71_72.json", "annex_l_schedule2_p73.json", "annex_l_schedule3_p74_75.json", "annex_l_schedule3_p76_77.json", "annex_l_schedule3_p78_79.json", "annex_l_schedule3_p80_81.json")
INPUTS += ("annex_l_schedule3_p82_83.json", "annex_l_schedule3_p84_85.json", "annex_l_schedule3_p86_87.json", "annex_l_schedule3_p88_89.json", "annex_l_schedule3_p90_91.json", "annex_l_schedule3_p92_93.json", "annex_l_schedule3_p94_95.json", "annex_l_schedule3_p96_97.json", "annex_l_schedule3_p98_99.json", "annex_l_schedule3_p100_101.json", "annex_l_schedule3_p102_103.json", "annex_l_schedule3_p104_105.json", "annex_l_schedule3_p106_107.json", "annex_l_schedule3_p108_109.json", "annex_l_schedule3_p110_111.json", "annex_l_schedule3_p112_113.json", "annex_l_schedule3_p114_115.json")
INPUTS += ("annex_l_schedule4_p116_117.json", "annex_l_schedule4_p118_119.json", "annex_l_schedule4_p120_121.json", "annex_l_schedule4_p122_123.json", "annex_l_schedule4_p124_125.json", "annex_l_schedule4_p126_127.json", "annex_l_schedule4_p128_129.json", "annex_l_schedule4_p130_131.json", "annex_l_schedule4_p132_133.json", "annex_l_schedule4_p134_135.json", "annex_l_schedule4_p136_137.json", "annex_l_schedule4_p138_139.json", "annex_l_schedule4_p140_141.json", "annex_l_schedule4_p142_143.json", "annex_l_schedule4_p144_145.json", "annex_l_schedule4_p146_147.json", "annex_l_schedule4_p148_149.json", "annex_l_schedule4_p150_151.json", "annex_l_schedule4_p152_153.json", "annex_l_schedule4_p154_155.json", "annex_l_schedule4_p156_157.json", "annex_l_schedule4_p158_159.json")
SCHEDULES = {
    1: {"pageStart": 2, "pageEnd": 57, "fiscalYear": 2024, "appropriationType": "current", "asOfDate": "2024-12-31"},
    2: {"pageStart": 58, "pageEnd": 73, "fiscalYear": 2024, "appropriationType": "continuing", "asOfDate": "2024-12-31"},
    3: {"pageStart": 74, "pageEnd": 115, "fiscalYear": 2025, "appropriationType": "current", "asOfDate": None},
    4: {"pageStart": 116, "pageEnd": 159, "fiscalYear": 2025, "appropriationType": "continuing", "asOfDate": None},
}
AMOUNT_FIELDS = (
    "authorizedAppropriationCentavos", "beginningBalanceCentavos", "gaaaoCentavos", "fisaroCentavos", "totalAllotmentsCentavos", "obligationsCentavos",
    "disbursementsCentavos", "unobligatedBalanceCentavos", "unpaidObligationsCentavos",
)


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


rows = []
seen_pages = set()
ordinals = Counter()
for filename in INPUTS:
    batch = read(filename)
    pages = {row["sourcePage"] for row in batch}
    if seen_pages & pages:
        raise ValueError(f"Overlapping Annex L project page batch: {filename}")
    seen_pages.update(pages)
    for source in batch:
        schedule = SCHEDULES[source["scheduleNumber"]]
        page = source["sourcePage"]
        if not schedule["pageStart"] <= page <= schedule["pageEnd"]:
            raise ValueError(f"Annex L page {page} does not belong to schedule {source['scheduleNumber']}")
        ordinals[page] += 1
        row = {
            "id": f"road-l-p{page:03d}-{ordinals[page]:03d}",
            "sourceAnnex": "L",
            "sourcePage": page,
            "printedPage": source["printedPage"],
            "sourcePdf": f"road-fund-pages/annex-l-p{page:03d}.pdf",
            "scheduleNumber": source["scheduleNumber"],
            "fiscalYear": schedule["fiscalYear"],
            "appropriationType": schedule["appropriationType"],
            "asOfDate": schedule["asOfDate"],
            "lineNumber": source["lineNumber"],
            "uacsCode": source.get("uacsCode"),
            "description": source["description"],
            "operatingUnit": source.get("operatingUnit"),
            **{key: source.get(key) for key in AMOUNT_FIELDS},
            "reviewNote": source.get("reviewNote"),
        }
        rows.append(row)

coverage = []
for number, schedule in SCHEDULES.items():
    subset = [row for row in rows if row["scheduleNumber"] == number]
    if not subset:
        continue
    pages = sorted({row["sourcePage"] for row in subset})
    entry = {
        "scheduleNumber": number,
        "transcribedPdfPages": pages,
        "recordCount": len(subset),
        "complete": pages == list(range(schedule["pageStart"], schedule["pageEnd"] + 1)),
    }
    if number == 3 and entry["complete"]:
        entry["reconciliation"] = {
            "status": "unresolved row-sum versus printed-header differences",
            "rowMinusPrintedCentavos": {
                "gaaaoCentavos": 2330200000,
                "fisaroCentavos": -2330200000,
                "obligationsCentavos": 5000,
                "unobligatedBalanceCentavos": -5000,
                "unpaidObligationsCentavos": 5000,
            },
            "audit": "../audit/annex_l_schedule3_reconciliation.md",
        }
    if number == 4 and entry["complete"]:
        entry["reconciliation"] = {
            "status": "row sums match repeated printed header in all five amount columns",
            "rowMinusPrintedCentavos": {
                "beginningBalanceCentavos": 0,
                "obligationsCentavos": 0,
                "disbursementsCentavos": 0,
                "unobligatedBalanceCentavos": 0,
                "unpaidObligationsCentavos": 0,
            },
        }
    coverage.append(entry)

payload = {"version": 1, "grain": "one Annex L project or particular line", "coverage": coverage, "records": rows}
(DATA / "road_fund_projects.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Built {len(rows)} Annex L project lines across {len(seen_pages)} pages")
