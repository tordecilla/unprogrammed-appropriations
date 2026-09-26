from pathlib import Path
import json
from playwright.sync_api import sync_playwright

Path('tmp').mkdir(exist_ok=True)

with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("http://127.0.0.1:18769/site/")
    page.locator("#results-body tr").first.wait_for()
    page.wait_for_function("document.querySelector('#ebudget-download')?.textContent.includes('transactions')")
    page.wait_for_function("document.querySelector('#road-fund-download')?.textContent.includes('rows')")
    assert f"{len(json.loads(Path('site/data/ebudget_transactions.json').read_text(encoding='utf-8'))['records']):,}" in page.locator("#ebudget-download").inner_text()
    assert f"{len(json.loads(Path('site/data/road_fund_projects.json').read_text(encoding='utf-8'))['records']):,}" in page.locator("#road-fund-download").inner_text()
    assert page.locator("#agency-filter").is_disabled()
    assert page.locator("#linked-filter").count() == 0
    assert page.locator("#agency-filter option").all_text_contents() == ["Select a department first"]
    assert "Department of Transportation" in page.locator("#department-filter").inner_text()
    assert page.locator("#sort").count() == 0
    assert page.locator(".table-particulars thead button").count() == 8
    assert len(set(page.locator(".table-particulars thead button").evaluate_all("buttons => buttons.map(button => getComputedStyle(button).fontSize)"))) == 1
    for column in ("saro-number", "department", "agency", "purpose", "particular", "date", "amount", "source"):
        button = page.locator(f'[data-sort="{column}"]')
        button.click()
        header = page.locator(f'[data-sort-column="{column}"]')
        initial_direction = "descending" if column in ("date", "amount") else "ascending"
        assert header.get_attribute("aria-sort") == initial_direction
        assert page.locator('.table-particulars thead [aria-sort="none"]').count() == 7
        button.click()
        assert header.get_attribute("aria-sort") != initial_direction
    page.locator('[data-sort="department"]').click()
    departments = page.locator("#results-body tr td:nth-child(2)").all_text_contents()
    assert departments == sorted(departments)
    page.locator('[data-sort="saro-number"]').click()
    assert page.evaluate("""() => {
      const values = [...document.querySelectorAll('#results-body tr td:first-child')].map(cell => cell.textContent.trim());
      const collator = new Intl.Collator(undefined, { numeric: true });
      return values.every((value, index) => !index || collator.compare(values[index - 1], value) <= 0);
    }""")
    top = [round(page.locator(selector).bounding_box()["y"]) for selector in ("#search", "#year-filter", "#department-filter", "#agency-filter", "#export-csv")]
    assert len(set(top)) == 1, top
    page.locator("#year-filter").select_option("2026")
    assert "2026" in page.locator("#results-body tr").first.inner_text()
    page.locator("#year-filter").select_option("all")
    page.locator("#department-filter").select_option("DOTr")
    assert page.locator("#agency-filter").is_enabled()
    agency_options = page.locator("#agency-filter option").all_text_contents()
    assert "Office of the Secretary" in agency_options
    assert "Bureau of Corrections" not in agency_options
    page.locator("#agency-filter").select_option(label="Office of the Secretary")
    rows = page.locator("#results-body tr")
    assert rows.count() > 0
    assert all("Department of Transportation" in row.inner_text() for row in rows.all())
    with page.expect_download() as download_info:
        page.locator("#export-csv").click()
    download = download_info.value
    csv_path = Path("tmp/filtered-normalized.csv")
    download.save_as(csv_path)
    csv = csv_path.read_text(encoding="utf-8-sig")
    assert "particular" in csv.splitlines()[0] and "purpose" in csv.splitlines()[0]
    assert "Department of Transportation" in csv
    assert "Department of Health" not in csv
    page.locator("#department-filter").select_option("all")
    assert page.locator("#agency-filter").is_disabled()
    page.locator("#department-filter").select_option("DAR")
    page.locator("#results-body tr").first.wait_for()
    pdf_link = page.locator("#results-body tr").first.locator("a", has_text="SARO PDF").first
    assert pdf_link.count() == 1
    href = pdf_link.get_attribute("href")
    assert href.startswith("https://github.com/tordecilla/unprogrammed-appropriations/releases/download/pdfs-documents-v1/")
    assert href.endswith(".pdf")
    page.locator("#department-filter").select_option("all")
    page.locator("#year-filter").select_option("2026")
    assert page.locator(".particular-cell").count() == 11
    with page.expect_download() as particulars_download:
        page.locator("#export-csv").click()
    particulars_path = Path("tmp/particulars-2026.csv")
    particulars_download.value.save_as(particulars_path)
    particulars_csv = particulars_path.read_text(encoding="utf-8-sig")
    assert "particular" in particulars_csv.splitlines()[0]
    assert len(particulars_csv.splitlines()) == 12
    assert not errors, errors
    page.screenshot(path="site/preview-desktop-top.png", full_page=False)
    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto("http://127.0.0.1:18769/site/")
    mobile.locator("#results-body tr").first.wait_for()
    assert mobile.locator('[data-sort="saro-number"]').is_visible()
    assert mobile.evaluate("document.documentElement.scrollWidth <= innerWidth")
    mobile.screenshot(path="site/preview-mobile-top.png", full_page=False)
    print("UI filters, dependent agency, CSV, standalone PDF, desktop and mobile: OK")
    browser.close()
