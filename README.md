# Unprogrammed Appropriations

A searchable index of Philippine Special Allotment Release Orders (SAROs), their particulars, and related 2024 unprogrammed appropriations records. The data was transcribed from the Philippine government's compliance annexes published in [G.R. No. 271059](https://sc.judiciary.gov.ph/g-r-no-271059-representative-edcel-c-lagman-et-al-v-the-congress-of-the-philippines-consisting-of-the-senate-of-the-philippines-represented-by-senate-president-juan-miguel-f-zubiri-and-the-h/).

**Published dashboard:** https://tordecilla.github.io/unprogrammed-appropriations/

The static dashboard lives in `site/`. Its source PDFs are published as individual GitHub release assets so readers can open a specific SARO or page without downloading a whole annex. The `site/data/` files hold the structured records and provenance links.

The GitHub Pages site is deployed from `site/` by the workflow in `.github/workflows/pages.yml`.

For PDF release, link-update, and redeployment steps, see [PUBLISHING.md](PUBLISHING.md).

## DPWH infrastructure drill-down

Choose **Explore DPWH infrastructure** to filter released attachment lines by infrastructure type and project region, with grouped amounts, project/SARO links and a filtered CSV. Share a filtered view using its URL (`?view=dpwh`). The drill-down follows the search, fiscal year and agency controls.

Classification in `site/dpwh.js` uses schedule headings, retaining combined or unspecified types and "Not identified" where headings are insufficient. The last regional heading takes precedence over an earlier Central Office/NCR heading. Regions describe project location; DEOs are not inferred from project names or locations. Totals cover available released project/claim attachment lines only, excluding signed SARO lines and four regional summary rows. They are not a complete measure of DPWH UA releases or expenditure.

Local validation: `node --check site/dpwh.js`, `node --check site/app_particulars.js` and `python tests/check_dpwh.py` (with a repository-root HTTP server on port 18769), plus the existing UI and SARO checks.
