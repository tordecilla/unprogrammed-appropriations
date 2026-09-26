from pathlib import Path
import hashlib, json, html
from urllib.parse import unquote, quote

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'court-documents'
OUT.mkdir(exist_ok=True)
DOWNLOADS = Path.home() / 'Downloads'
names = '''Petition-G.R.-271059.pdf
Consolidated-Comment-of-OSG-in-271059-and-271347.pdf
Amicus-Brief J. Salceda.pdf
F. Abad - Opening Remarks for Submission to SC.pdf
MBM Diokno - Presentation on Unprogrammed Appropriations.pdf
S. Monsod - Brief.pdf
Annex-A-Compliance-G.R.-No.-271059.pdf
Annex-B-Compliance-G.R.-No.271059.pdf
Annex-C-Compliance-G.R.-No.-271059.pdf
Annex-D-Compliance-G.R.-No.-271059.pdf
Annex-F-Compliance-G.R.-No.-271059.pdf
Annex-G-Compliance-G.R.-No.-271059.pdf
Annex-H-Compliance-G.R.-No.-271059.pdf
Annex-J-Compliance-G.R.-No.-271059.pdf
Annex-K-Compliance-G.R.-No.-271059.pdf
Annex-L-Compliance-G.R.-No.-271059.pdf
Annex-M-Compliance-G.R.-No.-271059.pdf
Annex-N-Compliance-G.R.-No.-271059.pdf
Annex-O-Compliance-G.R.-No.-271059.pdf
Annex-P-Compliance-G.R.-No.-271059.pdf
Compliance-G.R.-No.-271059.pdf
A NEP-2024-VOLUME-1_1-300.pdf
B NEP-2024-VOLUME-1_301-600.pdf
C-NEP-2024-VOLUME-1_601-900.pdf
D-NEP-2024-VOLUME-1_901-1200.pdf
E-NEP-2024-VOLUME-1_1201-1480.pdf
F NEP-2024-VOLUME-2.pdf
G NEP-2024-VOLUME-3.pdf
H NEP-2025-VOLUME-1_1-800.pdf
I NEP-2025-VOLUME-1_801-1526.pdf
J NEP-2025-VOLUME-2_1-500.pdf
K NEP-2025-VOLUME-2_501-1100.pdf
L NEP-2025-VOLUME-2_1101-1400.pdf
M NEP-2025-VOLUME-2_1401-1702.pdf
Motion-for-Leave-GR-NO.-271059-GR-NO.-271347-GR-NO.-E-02472-GR-NO.-E-04036.pdf
N NEP-2025-VOLUME-3_1-600.pdf
O NEP-2025-VOLUME-3_601-1140.pdf
P NEP-2026-VOLUME-1.pdf
Q NEP-2026-VOLUME-2.pdf
R-NEP-2026-VOLUME-3.pdf
S BESF-2024_compressed-1-450.pdf
T BESF-2024_compressed-451-896.pdf
U BESF-2025.pdf
W BESF-2026-1-550.pdf
Y BESF-2026-551-1110.pdf
Certified True Copy of the BCC Report on 2024.pdf
Certified True Copy of the BCC Report on 2025.pdf
Certified-True-Copy-of-the-BCC-Report-on-2026.pdf
CTCs of Treasurers Certifications-2023 2024  2025.pdf
Partial-Compliance-with-Motion-3-5-26.pdf
2024 GAA VOLUME 1-A  301-600 UPLOADED 1.pdf
2024 GAA VOLUME 1-A  601-900 UPLOADED.pdf
2024 GAA VOLUME 1-A 1-300 UPLOADED.pdf
2024 GAA VOLUME 1-A 901-1266 UPLOADED.pdf
2024 GAA VOLUME 1-B 1-500 UPLOADED.pdf
2024 GAA VOLUME 1-B 501-800.pdf
2024 GAA VOLUME 1-B 801-1069.pdf
2024 GAA VOLUME 1-C 1-600.pdf
2024 GAA VOLUME 1-C 601-1173.pdf
2024 GAA VOLUME 2-1-300.pdf
2024 GAA VOLUME 2-301-602.pdf
2025 GAA VOLUME 1-A_1-600.pdf
2025 GAA VOLUME 1-A_601-1280.pdf
2025 GAA VOLUME 1-B 1-600.pdf
2025 GAA VOLUME 1-B 601-1033.pdf
2025 GAA VOLUME 1-C - 601-1171.pdf
2025 GAA VOLUME 1-C-1-300.pdf
2025 GAA VOLUME 1-C-301-600.pdf
2025 GAA VOLUME 2.pdf
2026 GAA VOLUME 1-A.pdf
2026 GAA VOLUME 1-B.pdf
2026 GAA VOLUME 1-C.pdf
2026 GAA VOLUME 2.pdf
Budget process from preparation to accountability FILED.pdf
History Concept and Purpose of UA w table  FILED.pdf
Supplemental Compliance.pdf'''.splitlines()
http_indices = {22,28,29,32,41}
records = []
for i, name in enumerate(names):
    date = '2026/02' if i < 2 else '2026/04'
    url = f'https://sc.judiciary.gov.ph/wp-content/uploads/{date}/{quote(name)}'
    original = url.replace('https:', 'http:') if i in http_indices else url
    dest = OUT / name
    if not dest.exists():
        candidates = [DOWNLOADS / name, DOWNLOADS / quote(name)]
        for src in candidates:
            if src.is_file():
                data = src.read_bytes()
                if data.startswith(b'%PDF-') and b'%%EOF' in data[-4096:]:
                    dest.write_bytes(data)
                    break
    record = dict(filename=name, source_url=original, download_url=url, status='missing')
    if dest.exists():
        data = dest.read_bytes()
        record.update(status='verified', bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    records.append(record)
(OUT / 'manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
missing = [r for r in records if r['status']=='missing']
(ROOT / 'download-retries.html').write_text('<!doctype html><meta charset="utf-8"><title>Case document downloads</title><h1>Pending documents</h1>' + ''.join(f'<p><a href="{html.escape(r["download_url"])}">{html.escape(r["filename"])}</a></p>' for r in missing),encoding='utf-8')
print(json.dumps(dict(verified=len(records)-len(missing), expected=len(records), total_bytes=sum(r.get('bytes',0) for r in records),missing=[r['filename'] for r in missing]),indent=2))
