"""Link visually transcribed eBudget transaction rows to the SARO index."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


SITE = Path(__file__).parent
DATA = SITE / "data"
INPUTS = (
    "annex_c_ebudget_136_137.json",
    "annex_c_ebudget_138_139.json",
    "annex_c_ebudget_140_141.json",
    "annex_c_ebudget_142_143.json",
    "annex_c_ebudget_144_145.json",
    "annex_c_ebudget_146_147.json",
    "annex_c_ebudget_148_149.json",
    "annex_c_ebudget_150_151.json",
    "annex_c_ebudget_152_153.json",
    "annex_c_ebudget_154_155.json",
    "annex_c_ebudget_156_159.json",
    "annex_c_ebudget_160_163.json",
    "annex_c_ebudget_164_167.json",
    "annex_c_ebudget_168_171.json",
    "annex_c_ebudget_172_175.json",
    "annex_c_ebudget_176_179.json",
    "annex_c_ebudget_180_185.json",
    "annex_c_ebudget_186_191.json",
    "annex_c_ebudget_192_197.json",
    "annex_c_ebudget_198_203.json",
    "annex_c_ebudget_204_209.json",
    "annex_c_ebudget_210_215.json",
    "annex_c_ebudget_216_221.json",
    "annex_c_ebudget_222_227.json",
    "annex_c_ebudget_228_233.json",
    "annex_c_ebudget_234_239.json",
    "annex_c_ebudget_240_245.json",
    "annex_c_ebudget_246_251.json",
    "annex_c_ebudget_252_257.json",
    "annex_c_ebudget_258_263.json",
    "annex_c_ebudget_264_270.json",
    "annex_c_10508462_271_272_staging.json",
    "annex_c_10508462_273_274_staging.json",
    "annex_c_10508462_275_276_staging.json",
    "annex_c_10508462_277_278_staging.json",
    "annex_c_10508462_279_280_staging.json",
    "annex_c_10508462_281_282_staging.json",
    "annex_c_10508462_283_284_staging.json",
    "annex_c_10508462_285_286_staging.json",
    "annex_c_10508462_287_288_staging.json",
    "annex_c_10508462_289_290_staging.json",
    "annex_c_10508462_291_292_staging.json",
    "annex_c_10508462_293_294_staging.json",
    "annex_c_10508462_295_298_staging.json",
    "annex_c_10508462_299_302_staging.json",
    "annex_c_10508462_303_306_staging.json",
    "annex_c_10508462_307_310_staging.json",
    "annex_c_10508462_311_314_staging.json",
    "annex_c_10508462_315_318_staging.json",
    "annex_c_10508462_319_322_staging.json",
    "annex_c_10508462_323_326_staging.json",
    "annex_c_10508462_327_330_staging.json",
    "annex_c_10508462_331_334_staging.json",
    "annex_c_10508462_335_338_staging.json",
    "annex_c_10508462_339_344_staging.json",
    "annex_c_10508462_345_350_staging.json",
    "annex_c_10508462_351_356_staging.json",
    "annex_c_10508462_357_362_staging.json",
    "annex_c_10508462_363_368_staging.json",
    "annex_c_10508462_369_374_staging.json",
    "annex_c_10508462_375_380_staging.json",
    "annex_c_10508462_381_386_staging.json",
    "annex_c_10508462_387_392_staging.json",
    "annex_c_10508462_393_398_staging.json",
    "annex_c_10508462_399_404_staging.json",
    "annex_c_10508462_405_410_staging.json",
    "annex_c_10508462_411_416_staging.json",
    "annex_c_10508462_417_422_staging.json",
    "annex_c_10508462_423_428_staging.json",
    "annex_c_10508462_429_434_staging.json",
    "annex_c_10508462_435_440_staging.json",
    "annex_c_10508462_441_446_staging.json",
    "annex_c_10508462_447_452_staging.json",
    "annex_c_10508462_453_458_staging.json",
    "annex_c_10508462_459_464_staging.json",
    "annex_c_10508462_465_470_staging.json",
    "annex_c_10508462_471_476_staging.json",
    "annex_c_10508462_477_482_staging.json",
    "annex_c_10508462_483_488_staging.json",
    "annex_c_10508462_489_494_staging.json",
    "annex_c_10508462_495_500_staging.json",
    "annex_c_10508462_501_506_staging.json",
    "annex_c_10508462_507_512_staging.json",
    "annex_c_10508462_513_518_staging.json",
    "annex_c_10508462_519_524_staging.json",
    "annex_c_10508462_525_530_staging.json",
    "annex_c_10508462_531_536_staging.json",
    "annex_c_10508462_537_542_staging.json",
    "annex_c_10508462_543_548_staging.json",
    "annex_c_10508462_549_554_staging.json",
    "annex_c_10508462_555_560_staging.json",
    "annex_c_10508462_561_566_staging.json",
    "annex_c_10508462_567_572_staging.json",
    "annex_c_10508462_573_578_staging.json",
    "annex_c_10508462_579_584_staging.json",
    "annex_c_10508462_585_590_staging.json",
    "annex_c_10508462_591_596_staging.json",
    "annex_c_10508462_597_602_staging.json",
    "annex_c_10508462_603_608_staging.json",
    "annex_c_10508462_609_614_staging.json",
    "annex_c_10508462_615_620_staging.json",
    "annex_c_10508462_621_626_staging.json",
    "annex_c_10508462_627_632_staging.json",
    "annex_c_10508462_633_638_staging.json",
    "annex_c_10508462_639_644_staging.json",
    "annex_c_10508462_645_650_staging.json",
    "annex_c_10508462_651_656_staging.json",
    "annex_c_10508462_657_662_staging.json",
    "annex_c_10508462_663_668_staging.json",
    "annex_c_10508462_669_674_staging.json",
    "annex_c_10508462_675_680_staging.json",
    "annex_c_10508462_681_686_staging.json",
    "annex_c_10508462_687_692_staging.json",
    "annex_c_10508462_693_699_staging.json",
    "annex_c_10508462_700_705_staging.json",
    "annex_c_10508462_706_711_staging.json",
    "annex_c_10508462_712_717_staging.json",
    "annex_c_10508462_718_723_staging.json",
    "annex_c_10508462_724_729_staging.json",
    "annex_c_10508462_730_735_staging.json",
    "annex_c_10508462_736_738_staging.json",
    "annex_c_10508462_739_741_staging.json",
    "annex_c_10508462_742_744_staging.json",
    "annex_c_10508462_745_747_staging.json",
    "annex_c_10508462_748_750_staging.json",
    "annex_c_10508462_751_753_staging.json",
    "annex_c_10508462_754_756_staging.json",
    "annex_c_10508462_757_759_staging.json",
    "annex_c_10508462_760_762_staging.json",
    "annex_c_10508462_763_765_staging.json",
    "annex_c_10508462_766_768_staging.json",
    "annex_c_10508462_769_771_staging.json",
    "annex_c_10508462_772_774_staging.json",
    "annex_c_10508462_775_777_staging.json",
    "annex_c_10508462_778_780_staging.json",
    "annex_c_10508462_781_783_staging.json",
    "annex_c_10508462_784_786_staging.json",
    "annex_c_10508462_787_789_staging.json",
    "annex_c_10508462_790_795_staging.json",
    "annex_c_10508462_796_798_staging.json",
    "annex_f_10508462_p35_36.json",
    "annex_f_10508462_p37_38.json",
    "annex_f_10508462_p39_40.json",
    "annex_f_10508462_p41_42.json",
    "annex_f_10508462_p43_44.json",
    "annex_f_10508462_p45_46.json",
    "annex_f_10508462_p47_48.json",
    "annex_f_10508462_p49_50.json",
    "annex_f_10508462_p51_52.json",
    "annex_f_10508462_p53_58.json",
    "annex_f_10508462_p59_64.json",
    "annex_f_10508462_p65_70.json",
    "annex_f_10508462_p71_76.json",
    "annex_f_10508462_p77_82.json",
    "annex_f_10508462_p83_88.json",
    "annex_f_10508462_p89_94.json",
    "annex_f_10508462_p95_100.json",
    "annex_f_10508462_p101_106.json",
    "annex_f_10508462_p107_112.json",
    "annex_f_10508462_p113_118.json",
    "annex_f_10508462_p119_124.json",
    "annex_f_10508462_p125_130.json",
    "annex_f_10508462_p131_136.json",
    "annex_f_10508462_p137_142.json",
    "annex_f_10508462_p143_148.json",
    "annex_f_10508462_p149_154.json",
    "annex_f_10508462_p155_160.json",
    "annex_f_10508462_p161_166.json",
    "annex_f_10508462_p167_172.json",
    "annex_f_10508462_p173_176.json",
)
LISTING_TOTALS = {
    ("C", "10508463"): {"pageStart": 136, "pageEnd": 270, "transactionCount": 1153, "totalCentavos": 866_299_108_200},
    ("C", "10508462"): {"pageStart": 271, "pageEnd": 798, "transactionCount": 4166, "totalCentavos": 5_689_419_917_900},
    ("F", "10508462"): {"pageStart": 35, "pageEnd": 176, "transactionCount": 966, "totalCentavos": 2_044_742_049_900},
}


def read(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8-sig"))


def normal_number(value: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


def full_name(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+\([A-Z][A-Z0-9-]*\)$", "", value.strip())


def iso_date(value: str | None) -> str | None:
    if not value:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    return datetime.strptime(value, "%m/%d/%Y").date().isoformat()


documents = read("documents.json")["records"]
saros = read("saros.json")["records"]
by_signed_number = defaultdict(list)
by_list_number = defaultdict(list)
for row in documents:
    if row["type"] == "SARO" and row.get("saroNumber"):
        by_signed_number[normal_number(row["saroNumber"])].append(row)
for row in saros:
    if row.get("saroNumber"):
        by_list_number[normal_number(row["saroNumber"])].append(row)

rows = []
page_ordinals = Counter()
seen_pages = set()
for filename in INPUTS:
    batch = read(filename)
    batch_pages = {(row["sourceAnnex"], row.get("sourcePage", row.get("sourcePdfPage"))) for row in batch}
    if seen_pages & batch_pages:
        raise ValueError(f"Overlapping eBudget page batch: {filename}")
    seen_pages.update(batch_pages)
    for source in batch:
        code = source["sourceAnnex"]
        page = source.get("sourcePage", source.get("sourcePdfPage"))
        number = source["saroNumber"]
        normalized = normal_number(number)
        signed_matches = by_signed_number[normalized]
        list_matches = by_list_number[normalized]
        signed = signed_matches[0] if len(signed_matches) == 1 else None
        purpose_list = list_matches[0] if len(list_matches) == 1 else None
        page_ordinals[(code, page)] += 1
        ordinal = page_ordinals[(code, page)]
        funding_source = source.get("fundingSourceCode") or (source.get("fundingSource") or "").split("-", 1)[0]
        year = 2000 + int(re.search(r"-(\d{2})-\d+$", number).group(1))
        row = {
            "id": f"listing-{code.lower()}-p{page:03d}-{ordinal:03d}",
            "fiscalYear": year,
            "fundingSourceCode": funding_source,
            "sourceAnnex": code,
            "sourcePage": page,
            "printedPage": source["printedPage"],
            "sourcePdf": f"listing-pages/annex-{code.lower()}-p{page:03d}.pdf",
            "saroNumber": number,
            "barcodeNumber": source.get("barcodeNo", source.get("barcodeNumber")),
            "issueDate": iso_date(source.get("issueDate")),
            "department": full_name(source.get("department")),
            "sourceDepartment": source.get("department"),
            "agency": full_name(source.get("agency")),
            "sourceAgency": source.get("agency"),
            "organizationPath": source.get("organizationPath") or [],
            "particulars": source.get("particulars"),
            "purpose": source.get("purpose", source.get("purposeVisible")),
            "psCentavos": source["psCentavos"],
            "mooeCentavos": source["mooeCentavos"],
            "finexCentavos": source.get("finexCentavos", source.get("finExCentavos")),
            "coCentavos": source["coCentavos"],
            "totalCentavos": source["totalCentavos"],
            "saroType": source.get("saroType"),
            "status": source.get("status"),
            "statusDate": iso_date(source.get("statusDate")),
            "legalCode": source.get("legalCode"),
            "appropriationSource": source.get("appropriationSource"),
            "fundingCode": source.get("fundingCode"),
            "fundCodeSource": source.get("fundCodeSource"),
            "fundCodeRecipient": source.get("fundCodeRecipient"),
            "purposeListId": purpose_list["id"] if purpose_list else None,
            "signedDocumentId": signed["id"] if signed else None,
            "reviewNote": source.get("reviewNote"),
        }
        rows.append(row)

coverage = []
for code, source in sorted({(row["sourceAnnex"], row["fundingSourceCode"]) for row in rows}):
    subset = [row for row in rows if row["sourceAnnex"] == code and row["fundingSourceCode"] == source]
    reference = LISTING_TOTALS[(code, source)]
    pages = sorted({row["sourcePage"] for row in subset})
    all_pages_represented = pages == list(range(reference["pageStart"], reference["pageEnd"] + 1))
    total = sum(row["totalCentavos"] for row in subset)
    complete = all_pages_represented and len(subset) == reference["transactionCount"] and total == reference["totalCentavos"]
    entry = {
        "sourceAnnex": code,
        "fundingSourceCode": source,
        "transcribedPdfPages": pages,
        "transactionCount": len(subset),
        "transcribedTotalCentavos": total,
        "reportedTransactionCount": reference["transactionCount"],
        "reportedTotalCentavos": reference["totalCentavos"],
        "rowMinusReportedCount": len(subset) - reference["transactionCount"],
        "rowMinusReportedCentavos": total - reference["totalCentavos"],
        "allPagesRepresented": all_pages_represented,
        "complete": complete,
    }
    if (code, source) == ("C", "10508462") and all_pages_represented and not complete:
        entry["reconciliation"] = {
            "status": "unresolved row-sum versus printed-subtotal difference",
            "note": "annex_c_10508462_reconciliation_note.md",
            "rowMinusPrintedCentavos": total - reference["totalCentavos"],
        }
    coverage.append(entry)

payload = {"version": 1, "grain": "one eBudget SARO listing transaction", "coverage": coverage, "records": rows}
(DATA / "ebudget_transactions.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Built {len(rows)} eBudget transactions; {sum(bool(row['purposeListId']) for row in rows)} purpose-list and {sum(bool(row['signedDocumentId']) for row in rows)} signed-document links")
