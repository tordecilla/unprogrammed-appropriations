# Publishing the SARO index

The public repository is `tordecilla/unprogrammed-appropriations`. GitHub Pages deploys the `site/` directory from `main`. The source PDFs are deliberately **not** in Git or the Pages artifact: each has an individual GitHub Release URL. The original annexes are in `pdfs-annex-v1`; the smaller PDFs are grouped by their `site/` directory in releases such as `pdfs-documents-v1` and `pdfs-listing-pages-v1`. Keep the release assets public before publishing data that links to them.

GitHub CLI and Git commands that write `.git` need elevated execution on this computer. See `AGENTS.md`. The commands below assume PowerShell in the repository root and an authenticated `gh` session.

## Initial publication or a new PDF group

1. Put each original annex in `court-documents/` and each individual source PDF in the appropriate `site/<group>/` directory. The asset filename is part of the public URL, so keep it stable. PDFs are excluded from Git by `.gitignore`.
2. Create the original-annex release if needed: `gh release create pdfs-annex-v1 --repo tordecilla/unprogrammed-appropriations --target main --title 'Original compliance annexes' --notes 'Original compliance annex PDFs'`. Upload the 14 files named in `site/data/annexes.json` with `gh release upload pdfs-annex-v1 <files...> --repo tordecilla/unprogrammed-appropriations`.
3. Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\publish_pdf_releases.ps1` with elevation. It creates a release per `site/` PDF directory, uploads assets in batches, skips assets already present, and can be rerun after interruption. GitHub permits at most 1,000 assets per release, so keep groups below that limit.
4. Run `powershell -NoProfile -ExecutionPolicy Bypass -File .\verify_pdf_releases.ps1` with elevation. It compares every local PDF filename against the release assets, including the 14 original annexes. Test a few direct release URLs, including an original annex, a SARO, and a page PDF.
5. Run `python site/publish_links.py --write`. This replaces local PDF paths in `site/data/*.json` and `site/data/*.csv` with release URLs and sets each annex's `releaseUrl`. Run `python site/publish_links.py` again: it should report zero rewrites. The dashboard JavaScript uses `annexes.json` for links to full annexes.
6. Validate the local site: run `node --check site/app_particulars.js` and `node --check site/saro.js`, then start `python -m http.server 18769` from the repository root. In another terminal run `python tests/check_ui.py` and `python tests/check_saro_tables.py`; stop the temporary server afterward. The UI checks require Playwright and Chromium. Confirm source links point to `github.com/tordecilla/unprogrammed-appropriations/releases/download/` and that the site loads without local PDFs.
7. Commit the site, data, workflow, scripts, and documentation on `main`, then push. `.github/workflows/pages.yml` uploads `site/` and deploys it to Pages. Check the workflow run and open `https://tordecilla.github.io/unprogrammed-appropriations/` to verify the live table, a SARO page, CSV downloads, and source PDFs.

## Later updates

1. Update the structured data and any corresponding local PDFs. Regenerate individual page/SARO PDFs with the relevant `site/export_*.py` script when source boundaries change. Confirm their filenames and links in the data.
2. If only **new filenames** are added, rerun `publish_pdf_releases.ps1`; it uploads the new assets to the current group release. If an **existing PDF's content changes**, do not silently replace its published asset. Increment that group's release tag (for example, `pdfs-documents-v2`) in both `publish_pdf_releases.ps1` and `PDF_GROUPS` in `site/publish_links.py`, then upload the group to the new release. For an original annex change, create and upload a new `pdfs-annex-vN` release manually and update the `court-documents` mapping. The link script can remap data URLs from an older release tag to the new tag.
3. Run the link script, local checks, and release verification above. Commit and push. The Pages workflow redeploys on a `main` push; verify the live site after it completes.

For repeatable updates, do not edit the public JSON or CSV links by hand. `site/publish_links.py` is the source of truth for release URL construction.
