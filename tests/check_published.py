"""Smoke-check the deployed Pages site and representative release PDF URLs."""

import json
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright


base = 'https://tordecilla.github.io/unprogrammed-appropriations/'
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(accept_downloads=True)
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(base, wait_until='domcontentloaded')
    page.locator('#results-body tr').first.wait_for(timeout=60000)
    assert page.locator('#result-count').inner_text().endswith('records')
    assert page.locator('.table-particulars thead button').count() == 8
    assert page.locator('#results-body .source-links a').first.get_attribute('href').startswith('https://github.com/tordecilla/unprogrammed-appropriations/releases/download/')
    with page.expect_download() as download_info:
        page.locator('#export-csv').click()
    assert download_info.value.suggested_filename.endswith('.csv')
    page.goto(base + 'saro.html?id=B-p114', wait_until='domcontentloaded')
    page.locator('[data-detail-table="schedule"]').wait_for(timeout=60000)
    assert page.locator('[data-table-search="particulars"]').count() == 1
    assert page.locator('[data-table-search="schedule"]').count() == 1
    assert page.locator('[data-table-search="status"]').count() == 1
    with page.expect_download() as download_info:
        page.locator('[data-table-export="schedule"]').click()
    assert download_info.value.suggested_filename.endswith('-schedule.csv')
    assert not errors, errors
    browser.close()

data = Path('site/data')
urls = [
    json.loads((data / 'annexes.json').read_text(encoding='utf-8'))['records'][0]['releaseUrl'],
    json.loads((data / 'documents.json').read_text(encoding='utf-8'))['records'][0]['standalonePdf'],
    json.loads((data / 'ebudget_transactions.json').read_text(encoding='utf-8'))['records'][0]['sourcePdf'],
]
for url in urls:
    with urllib.request.urlopen(urllib.request.Request(url, method='HEAD'), timeout=30) as response:
        assert response.status == 200, (url, response.status)
print('Published Pages site, SARO detail, and representative source PDFs: OK')
