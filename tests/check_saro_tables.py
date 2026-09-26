import csv
from pathlib import Path

from playwright.sync_api import sync_playwright

Path('tmp').mkdir(exist_ok=True)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:18769/site/saro.html?id=B-p114")
    page.locator('[data-detail-table="schedule"] tbody tr').first.wait_for()
    assert page.locator('.project-note, .project-coverage').count() == 0
    for key in ("particulars", "schedule", "status"):
        table = page.locator(f'[data-detail-table="{key}"]')
        search = page.locator(f'[data-table-search="{key}"]')
        count = page.locator(f'[data-table-count="{key}"]')
        assert table.count() == search.count() == count.count() == 1
        initial = table.locator('tbody tr:not(.filter-empty)').count()
        assert initial > 0
        search.fill('zzznomatch')
        assert count.inner_text().startswith(f'0 of {initial}')
        assert table.locator('tbody tr.filter-empty').is_visible()
        with page.expect_download() as download_info:
            page.locator(f'[data-table-export="{key}"]').click()
        path = Path(f'tmp/saro-{key}-empty.csv')
        download_info.value.save_as(path)
        assert len(list(csv.reader(path.open(encoding='utf-8-sig', newline='')))) == 1
        search.fill('')
        assert count.inner_text().startswith(f'{initial} of {initial}')
        term = table.locator('tbody tr:not(.filter-empty)').first.locator('td').nth(1 if key != 'status' else 0).inner_text().strip()[:32]
        search.fill(term)
        visible = table.locator('tbody tr:not(.filter-empty):visible').count()
        assert 0 < visible <= initial
        with page.expect_download() as download_info:
            page.locator(f'[data-table-export="{key}"]').click()
        path = Path(f'tmp/saro-{key}-filtered.csv')
        download_info.value.save_as(path)
        assert len(list(csv.reader(path.open(encoding='utf-8-sig', newline='')))) == visible + 1
    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto("http://127.0.0.1:18769/site/saro.html?id=B-p114")
    mobile.locator('[data-table-search="schedule"]').wait_for()
    assert mobile.evaluate('document.documentElement.scrollWidth <= innerWidth')
    assert not errors, errors
    browser.close()
    print('SARO table filters, counts, CSV exports, and mobile layout: OK')
