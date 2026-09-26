"""Replace local source-PDF paths in the public data payload with release URLs.

Run from the repository root: python site/publish_links.py --write
"""

import argparse
import csv
import json
import re
from pathlib import Path
from urllib.parse import quote, unquote


ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DATA = SITE / "data"
REPO = "tordecilla/unprogrammed-appropriations"
PDF_GROUPS = {
    "court-documents": "pdfs-annex-v1",
    "documents": "pdfs-documents-v1",
    "advice-pages": "pdfs-advice-pages-v1",
    "agency-expenditure-pages": "pdfs-agency-expenditure-pages-v1",
    "debt-pages": "pdfs-debt-pages-v1",
    "listing-pages": "pdfs-listing-pages-v1",
    "process-pages": "pdfs-process-pages-v1",
    "project-pages": "pdfs-project-pages-v1",
    "revenue-pages": "pdfs-revenue-pages-v1",
    "road-fund-pages": "pdfs-road-fund-pages-v1",
    "status-pages": "pdfs-status-pages-v1",
}
LOCAL_PDF = re.compile(r"^(?P<group>[^/:]+?)/(?P<filename>[^/#?]+\.pdf)(?P<fragment>#.*)?$", re.I)
RELEASE_PDF = re.compile(rf"^https://github\.com/{REPO}/releases/download/(?P<tag>pdfs-[^/]+)/(?P<filename>[^#?]+\.pdf)(?P<fragment>#.*)?$", re.I)


def release_url(group: str, filename: str) -> str:
    return f"https://github.com/{REPO}/releases/download/{PDF_GROUPS[group]}/{quote(filename, safe='')}"


def rewrite(value, changed: list[int]):
    if isinstance(value, dict):
        return {key: rewrite(item, changed) for key, item in value.items()}
    if isinstance(value, list):
        return [rewrite(item, changed) for item in value]
    if not isinstance(value, str):
        return value
    local = LOCAL_PDF.fullmatch(value)
    if local and local["group"] in PDF_GROUPS:
        group, filename, fragment = local["group"], local["filename"], local["fragment"] or ""
    else:
        remote = RELEASE_PDF.fullmatch(value)
        if not remote:
            return value
        group = next((name for name in PDF_GROUPS if re.fullmatch(rf"{re.escape(PDF_GROUPS[name].rsplit('-v', 1)[0])}-v\d+", remote["tag"])), None)
        if not group:
            return value
        filename, fragment = unquote(remote["filename"]), remote["fragment"] or ""
    source = (ROOT if group == "court-documents" else SITE) / group / filename
    if not source.is_file():
        raise FileNotFoundError(f"Referenced PDF is missing: {source}")
    updated = release_url(group, filename) + fragment
    if updated != value:
        changed[0] += 1
    return updated


def main(write: bool) -> None:
    changed = [0]
    touched = []
    for path in sorted(DATA.glob("*.json")):
        raw = path.read_text(encoding="utf-8-sig")
        obj = json.loads(raw)
        updated = rewrite(obj, changed)
        if path.name == "annexes.json":
            for annex in updated["records"]:
                annex["releaseUrl"] = release_url("court-documents", annex["file"])
        if updated != obj:
            touched.append(path)
            if write:
                path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for path in sorted(DATA.glob("*.csv")):
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.reader(handle)
            rows = list(reader)
        updated = [[rewrite(cell, changed) for cell in row] for row in rows]
        if updated != rows:
            touched.append(path)
            if write:
                with path.open("w", encoding="utf-8-sig", newline="") as handle:
                    csv.writer(handle, lineterminator="\r\n").writerows(updated)
    print(f"{'Rewrote' if write else 'Would rewrite'} {changed[0]:,} PDF links across {len(touched)} data files.")
    if not write and touched:
        print("Files with local PDF links:", ", ".join(path.name for path in touched))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="update the data files in place")
    args = parser.parse_args()
    main(args.write)
