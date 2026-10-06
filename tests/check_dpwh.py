"""Check DPWH totals against source lines and exercise the drill-down."""
import csv
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

projects = json.loads(Path('site/data/project_items.json').read_text(encoding='utf-8'))['records']
documents = {row['id']: row for row in json.loads(Path('site/data/documents.json').read_text(encoding='utf-8'))['records']}
eligible = [row for row in projects if row['departmentCode'] == 'DPWH' and row['itemLevel'] != 'regional_summary' and documents[row['signedDocumentId']]['amountStage'] == 'released']
Path('tmp').mkdir(exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto('http://127.0.0.1:18769/site/')
    page.locator('#dpwh-toggle').wait_for()
    page.locator('#dpwh-toggle').click()
    assert page.locator('#department-filter').input_value() == 'DPWH'
    actual = page.evaluate("filteredLines().reduce((sum, row) => sum + row.line.amountCentavos, 0)")
    assert actual == sum(row['amountCentavos'] for row in eligible)
    assert page.evaluate('filteredLines().length') == len(eligible)
    assert len(eligible) == 2024
    # More specific region overrides the Central Office/NCR heading.
    assert page.evaluate("DPWH.classify({programPath: ['National Capital Region', 'Central Office', 'Region III']}).region") == 'Region III'
    assert page.evaluate("DPWH.classify({programPath: ['NCR (Attachment B)', 'CAR']}).region") == 'Cordillera Administrative Region'
    assert page.evaluate("DPWH.classify({description: 'Road in Camarines Sur', programPath: []}).region") == 'Not identified'
    assert page.evaluate("DPWH.classify({programPath: ['For Payment of Right-of-Way', 'Flood Control']}).type") == 'Right-of-way claims'
    page.locator('[data-dpwh-group="infra"][data-value="Flood control and drainage"]').click()
    assert page.locator('#infra-filter').input_value() == 'Flood control and drainage'
    assert page.locator('[data-dpwh-group="region"]').count() > 0
    page.locator('[data-dpwh-group="region"][data-value="Region III"]').click()
    expected = page.evaluate("filteredLines().map(row => ({id:row.line.id, amount:row.line.amountCentavos}))")
    assert expected
    assert page.evaluate("filteredLines().every(row => DPWH.classify(row.line).type === 'Flood control and drainage' && DPWH.classify(row.line).region === 'Region III')")
    with page.expect_download() as info:
        page.locator('#export-csv').click()
    info.value.save_as('tmp/dpwh-filtered.csv')
    with Path('tmp/dpwh-filtered.csv').open(encoding='utf-8-sig', newline='') as file:
        records = list(csv.DictReader(file))
    assert {row['line_id'] for row in records} == {row['id'] for row in expected}
    assert sum(int(row['line_amount_centavos']) for row in records) == sum(row['amount'] for row in expected)
    assert all(row['infra_type_from_schedule'] == 'Flood control and drainage' and row['region_from_schedule'] == 'Region III' for row in records)
    page.reload()
    page.locator('#infra-filter').wait_for()
    assert page.locator('#region-filter').input_value() == 'Region III'
    assert page.evaluate('filteredLines().length') == len(expected)
    page.screenshot(path='tmp/dpwh-desktop.png', full_page=False)
    # Detail and back navigation preserve the drill-down.
    page.locator('#results-body .saro-number-link').first.click()
    page.locator('.back').wait_for()
    page.locator('.back').click()
    page.locator('#infra-filter').wait_for()
    assert page.locator('#region-filter').input_value() == 'Region III'
    page.locator('#year-filter').select_option('2026')
    assert page.evaluate('filteredLines().length') == 0
    assert page.locator('.dpwh-total strong').inner_text().endswith('0')
    page.locator('#year-filter').select_option('all')
    page.locator('#search').fill('no-such-project-xyz')
    assert page.evaluate('filteredLines().length') == 0
    page.locator('#search').fill('')
    page.locator('#department-filter').select_option('DOTr')
    assert page.locator('#infra-filter').count() == 0
    assert 'view=dpwh' not in page.url
    mobile = browser.new_page(viewport={'width':390,'height':844})
    mobile.goto('http://127.0.0.1:18769/site/?view=dpwh')
    mobile.locator('#infra-filter').wait_for()
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth')
    mobile.locator('#infra-filter').select_option('Bridges')
    assert mobile.evaluate('filteredLines().every(row => DPWH.classify(row.line).type === "Bridges")')
    mobile.screenshot(path='tmp/dpwh-mobile.png', full_page=True)
    assert not errors, errors
    browser.close()
print('DPWH source totals, type/region filters, CSV, URLs, detail navigation, empty states and mobile: OK')
