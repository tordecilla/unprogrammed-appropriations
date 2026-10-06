const initial = new URLSearchParams(location.search);
const state = { query: initial.get('q') || '', year: initial.get('year') || 'all', department: initial.get('department') || 'all', agency: initial.get('agency') || 'all', sort: initial.get('sort') || 'list', page: Math.max(1, Number(initial.get('page')) || 1) };
state.dpwh = initial.get('view') === 'dpwh';
state.infra = initial.get('infra') || 'all';
state.region = initial.get('region') || 'all';
if (state.dpwh) state.department = 'DPWH';
const data = { saros: [], documents: [], sources: [], particulars: [], projects: [], discrepancies: [], rows: [] };
const PAGE_SIZE = 25;
const SORT_COLUMNS = ['saro-number', 'department', 'agency', 'purpose', 'particular', 'date', 'amount', 'source'];
const DEFAULT_SORT_DIRECTION = { date: 'desc', amount: 'desc' };
const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const pesos = (number) => number == null ? '—' : `₱${new Intl.NumberFormat('en-PH', { maximumFractionDigits: 0 }).format(number)}`;
const centavos = (number) => number == null ? '—' : `₱${new Intl.NumberFormat('en-PH', { minimumFractionDigits: number % 100 ? 2 : 0, maximumFractionDigits: 2 }).format(number / 100)}`;
const documentById = (id) => data.documents.find((document) => document.id === id);
const pdf = (code, page) => { const source = data.sources.find((item) => item.id === `annex-${String(code).toLowerCase()}`); return source ? `${source.releaseUrl || `../court-documents/${encodeURIComponent(source.file)}`}#page=${page}` : '#'; };
const documentPdf = (document) => document?.standalonePdf || (document ? pdf(document.annexId, document.pageStart) : '');
function filterSearch() {
  const params = new URLSearchParams();
  if (state.dpwh) params.set('view', 'dpwh');
  if (state.dpwh && state.infra !== 'all') params.set('infra', state.infra);
  if (state.dpwh && state.region !== 'all') params.set('region', state.region);
  if (state.query) params.set('q', state.query);
  if (state.year !== 'all') params.set('year', state.year);
  if (state.department !== 'all') params.set('department', state.department);
  if (state.agency !== 'all') params.set('agency', state.agency);
  if (state.sort !== 'list') params.set('sort', state.sort);
  if (state.page > 1) params.set('page', String(state.page));
  return params.size ? `?${params}` : '';
}
const detailHref = (id, projectId) => `saro.html?id=${encodeURIComponent(id)}${filterSearch() ? `&from=${encodeURIComponent(filterSearch())}` : ''}${projectId ? `#project-${encodeURIComponent(projectId)}` : ''}`;
function syncUrl() { history.replaceState(null, '', `${location.pathname}${filterSearch()}`); }

function makeRows() {
  const byOrder = new Map(data.saros.filter((item) => item.orderDocumentId).map((item) => [item.orderDocumentId, item]));
  const byCandidate = new Map(data.saros.flatMap((item) => (item.candidateOrderDocumentIds || []).map((id) => [id, item])));
  const departments = new Map(data.saros.filter((item) => item.departmentCode).map((item) => [item.departmentCode, item.department]));
  const particularRows = data.particulars.map((line) => {
    const document = documentById(line.documentId);
    const parent = byOrder.get(line.documentId) || byCandidate.get(line.documentId);
    const formDepartment = String(document?.formDepartment || '').replace(/\s*\([^)]*\)\s*$/, '');
    const formDepartmentEntry = [...departments].find(([, name]) => name.toLowerCase() === formDepartment.toLowerCase());
    const yearFromNumber = Number(String(document?.saroNumber || '').match(/-(\d\d)-/)?.[1]);
    return { kind: 'particular', line, document, parent, candidateMatch: !byOrder.has(line.documentId) && byCandidate.has(line.documentId), saroNumber: document?.saroNumber || line.saroNumber,
      fiscalYear: parent?.fiscalYear || Number(String(document?.date || '').slice(0, 4)) || (yearFromNumber ? 2000 + yearFromNumber : null),
      departmentCode: parent?.departmentCode || formDepartmentEntry?.[0] || null,
      department: parent?.department || formDepartmentEntry?.[1] || formDepartment || null,
      agency: parent?.agency || document?.formAgency || document?.agency || null,
      date: parent?.date || document?.date || null,
      purpose: parent?.purpose || document?.formPurpose || document?.purpose || null,
    };
  });
  const withParticulars = new Set(data.particulars.map((line) => line.documentId));
  const projectRows = data.projects.map((line) => {
    const document = documentById(line.signedDocumentId);
    const parent = data.saros.find((item) => item.id === line.purposeListId);
    return { kind: 'project', line, document, parent, candidateMatch: false,
      saroNumber: line.saroNumber, fiscalYear: line.fiscalYear, departmentCode: line.departmentCode,
      department: line.department, agency: line.agency, date: parent?.date || document?.date || null, purpose: line.purpose };
  });
  const purposeOnly = data.saros.filter((item) => !withParticulars.has(item.orderDocumentId)).map((item) => ({
    kind: 'purpose', line: null, document: documentById(item.orderDocumentId), parent: item, candidateMatch: false,
    saroNumber: item.saroNumber, fiscalYear: item.fiscalYear, departmentCode: item.departmentCode,
    department: item.department, agency: item.agency, date: item.date, purpose: item.purpose,
  }));
  return [...particularRows, ...projectRows, ...purposeOnly];
}

function matches(row, text) {
  if (state.year !== 'all' && String(row.fiscalYear) !== state.year) return false;
  if (state.department !== 'all' && (row.departmentCode || '__none__') !== state.department) return false;
  if (state.department !== 'all' && state.agency !== 'all' && row.agency !== state.agency) return false;
  const query = state.query.trim().toLowerCase();
  return !query || text.toLowerCase().includes(query);
}

function filteredLines() {
  const rows = data.rows.filter((row) => (!state.dpwh || (DPWH.eligible(row) && (state.infra === 'all' || DPWH.classify(row.line).type === state.infra) && (state.region === 'all' || DPWH.classify(row.line).region === state.region))) && matches(row, [row.saroNumber, row.department, row.departmentCode, row.agency, row.date, row.purpose, row.line?.description, row.line?.adviceParticular, row.line?.mfoPapCode, row.line?.objectCode, row.line?.uacsCode, ...(row.line?.programPath || [])].join(' ')));
  const listOrder = (a, b) => a.fiscalYear - b.fiscalYear || (a.parent?.listNumber ?? 9999) - (b.parent?.listNumber ?? 9999) || (a.document?.pageStart ?? 9999) - (b.document?.pageStart ?? 9999) || (a.line?.lineNumber ?? 0) - (b.line?.lineNumber ?? 0);
  if (state.sort === 'list') return rows.sort(listOrder);
  const column = SORT_COLUMNS.find((name) => state.sort === `${name}-asc` || state.sort === `${name}-desc`);
  const direction = state.sort.endsWith('-desc') ? 'desc' : 'asc';
  const value = (row) => ({
    'saro-number': row.saroNumber, department: row.department, agency: row.agency,
    purpose: row.purpose, particular: row.line?.description, date: row.date,
    amount: row.line?.amountCentavos ?? (row.line?.amountPesos == null ? null : row.line.amountPesos * 100),
    source: row.kind === 'purpose' ? `${row.parent?.sourceAnnex || ''}-${String(row.parent?.sourcePage ?? 0).padStart(5, '0')}` : row.kind === 'project' ? `${row.line?.sourceAnnex || ''}-${String(row.line?.sourcePage ?? 0).padStart(5, '0')}` : `${row.document?.annexId || ''}-${String(row.document?.pageStart ?? 0).padStart(5, '0')}`,
  })[column];
  const collator = new Intl.Collator('en', { numeric: true, sensitivity: 'base' });
  rows.sort((a, b) => {
    const left = value(a), right = value(b);
    if (left == null || left === '') return right == null || right === '' ? listOrder(a, b) : 1;
    if (right == null || right === '') return -1;
    const compared = column === 'amount' ? left - right : collator.compare(String(left), String(right));
    return (direction === 'desc' ? -compared : compared) || listOrder(a, b);
  });
  return rows;
}

function sortHeader(column, label, extraClass = '') {
  return `<th scope="col" class="${extraClass}" data-sort-column="${column}" aria-sort="none"><button type="button" data-sort="${column}" aria-label="Sort by ${label}">${label}<span class="sort-indicator" aria-hidden="true"></span></button></th>`;
}

function updateSortHeaders() {
  document.querySelectorAll('[data-sort-column]').forEach((header) => {
    const direction = state.sort === `${header.dataset.sortColumn}-asc` ? 'ascending' : state.sort === `${header.dataset.sortColumn}-desc` ? 'descending' : 'none';
    header.setAttribute('aria-sort', direction);
    header.querySelector('button').setAttribute('aria-label', `${header.textContent.trim()}${direction === 'none' ? ', sort' : `, sorted ${direction}; activate to reverse`}`);
  });
}

function sourceLink(label, code, first, last = first, href = pdf(code, first), note = '') {
  const range = last > first ? `pp.${first}–${last}` : `p.${first}`;
  return `<a href="${esc(href)}" target="_blank" rel="noopener" title="${esc(note || `Annex ${code}, original PDF ${range}`)}">${esc(label)} PDF · ${esc(code)} ${esc(range)} ↗</a>`;
}

function lineSources(row) {
  const links = [];
  if (row.kind === 'purpose') return purposeSources(row.parent);
  if (row.kind === 'project') links.push(sourceLink('Schedule', row.line.sourceAnnex, row.line.sourcePage, row.line.sourcePage, row.line.sourcePdf));
  if (row.document) links.push(sourceLink('SARO', row.document.annexId, row.document.pageStart, row.document.pageEnd, documentPdf(row.document)));
  for (const evidence of row.document?.statusEvidence || []) links.push(sourceLink('Advice', row.document.annexId, evidence.sourcePage, evidence.sourcePage, evidence.sourcePdf));
  if (row.line?.adviceSourcePdf) links.push(sourceLink('Advice', row.line.sourceAnnex, row.line.adviceSourcePage, row.line.adviceSourcePage, row.line.adviceSourcePdf));
  if (row.parent) links.push(sourceLink(row.candidateMatch ? 'Compare list' : 'List', row.parent.sourceAnnex, row.parent.sourcePage, row.parent.sourcePage, pdf(row.parent.sourceAnnex, row.parent.sourcePage), row.candidateMatch ? row.parent.candidateOrderNote : ''));
  return `<div class="source-links">${links.join('')}</div>`;
}

function purposeSources(item) {
  const links = [sourceLink('List', item.sourceAnnex, item.sourcePage)];
  const order = documentById(item.orderDocumentId);
  if (order) links.push(sourceLink('SARO', order.annexId, order.pageStart, order.pageEnd, documentPdf(order)));
  for (const id of item.candidateOrderDocumentIds || []) {
    const candidate = documentById(id);
    if (candidate) links.push(sourceLink('Compare SARO', candidate.annexId, candidate.pageStart, candidate.pageEnd, documentPdf(candidate), item.candidateOrderNote));
  }
  return `<div class="source-links">${links.join('')}</div>`;
}

function lineHtml(row) {
  const path = (row.line?.programPath || []).filter(Boolean).join(' › ');
  const codes = [row.line?.mfoPapCode && `MFO/PAP ${row.line.mfoPapCode}`, row.line?.objectCode && `Object ${row.line.objectCode}`, row.line?.uacsCode && `UACS ${row.line.uacsCode}`].filter(Boolean).join(' · ');
  const number = row.document ? `<a class="saro-number-link" href="${detailHref(row.document.id, row.kind === 'project' ? row.line.id : null)}">${esc(row.saroNumber || '—')}</a>` : esc(row.saroNumber || `Entry ${row.parent?.sourceAnnex}-${row.parent?.listNumber ?? 'unnumbered'}`);
  const amount = row.kind === 'project' ? centavos(row.line.amountCentavos) : pesos(row.line?.amountPesos);
  return `<tr><td data-label="SARO number" class="mono">${number}</td><td data-label="Department">${esc(row.department || '—')}</td><td data-label="Agency">${esc(row.agency || '—')}</td><td data-label="Purpose"><div class="purpose-full">${esc(row.purpose || '—')}</div></td><td data-label="Particular" class="particular-cell">${row.line ? `<small class="line-type">${row.kind === 'project' ? (row.line.itemLevel === 'regional_summary' ? 'Regional summary' : 'Attached schedule line') : 'Signed SARO line'}</small><span class="particular-title">${esc(row.line.description || '—')}</span>${row.document?.amountStage === 'status_unresolved' ? '<small>Form marked CANCELLED · status unresolved</small>' : ''}${row.line.adviceParticular ? `<small>Advice detail: ${esc(row.line.adviceParticular)}</small>` : ''}${path ? `<small>${esc(path)}</small>` : ''}${codes ? `<small class="mono">${esc(codes)}</small>` : ''}` : '<span class="no-particular">—</span>'}</td><td data-label="Date" class="mono">${esc(row.date || '—')}</td><td data-label="Line amount" class="amount">${esc(amount)}</td><td data-label="Source">${lineSources(row)}</td></tr>`;
}

function renderRows() {
  const focusedControl = ['infra-filter', 'region-filter'].includes(document.activeElement?.id) ? document.activeElement.id : null;
  const rows = filteredLines();
  updateSortHeaders();
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  state.page = Math.min(state.page, pages);
  syncUrl();
  renderDpwh();
  if (focusedControl) document.getElementById(focusedControl)?.focus({ preventScroll: true });
  $('#results-body').innerHTML = rows.length ? rows.slice((state.page - 1) * PAGE_SIZE, state.page * PAGE_SIZE).map(lineHtml).join('') : '<tr><td colspan="8" class="empty">No matching records.</td></tr>';
  const first = rows.length ? (state.page - 1) * PAGE_SIZE + 1 : 0;
  const last = Math.min(state.page * PAGE_SIZE, rows.length);
  $('#result-count').textContent = `${rows.length.toLocaleString()} ${rows.length === 1 ? 'record' : 'records'}`;
  $('#result-range').textContent = rows.length
    ? `of ${data.rows.length.toLocaleString()} total · showing ${first.toLocaleString()}–${last.toLocaleString()}`
    : `of ${data.rows.length.toLocaleString()} total`;
  $('#pager').innerHTML = rows.length > PAGE_SIZE ? `<button type="button" data-page="prev" ${state.page === 1 ? 'disabled' : ''} aria-label="Previous page">←</button><span>${state.page} / ${pages}</span><button type="button" data-page="next" ${state.page === pages ? 'disabled' : ''} aria-label="Next page">→</button>` : '';
}


function renderDpwh() {
  const panel = $('#dpwh-panel');
  if (!state.dpwh) {
    panel.innerHTML = '<button type="button" id="dpwh-toggle" class="filter">Explore DPWH infrastructure &rarr;</button>';
    panel.classList.remove('expanded');
    return;
  }
  panel.classList.add('expanded');
  const eligible = data.rows.filter(DPWH.eligible);
  const options = (key, current, label) => `<option value="all">${label}</option>${[...new Set(eligible.map(row => DPWH.classify(row.line)[key]))].sort((a,b) => a.localeCompare(b, 'en', { numeric: true })).map(value => `<option value="${esc(value)}" ${value === current ? 'selected' : ''}>${esc(value)}</option>`).join('')}`;
  const rows = filteredLines();
  const total = rows.reduce((sum,row) => sum + row.line.amountCentavos, 0);
  const groupKey = state.infra === 'all' ? 'type' : 'region';
  const groups = new Map();
  for (const row of rows) {
    const name = DPWH.classify(row.line)[groupKey];
    const entry = groups.get(name) || { count: 0, amount: 0 };
    entry.count++; entry.amount += row.line.amountCentavos; groups.set(name, entry);
  }
  const max = Math.max(1, ...[...groups.values()].map(item => item.amount));
  panel.innerHTML = `<div class="dpwh-head"><div><div class="eyebrow">DPWH &middot; ATTACHED PROJECT SCHEDULES</div><h2>Explore infrastructure releases</h2></div><button type="button" id="dpwh-toggle" class="filter">Back to all DPWH records</button></div>
    <p class="dpwh-note">Available released SARO attachment lines only; not all DPWH UA releases, obligations or spending. Four regional summary rows are excluded. Types are grouped from schedule headings; region uses the last regional heading, which describes project location, not the implementing DEO. Unclear entries remain &ldquo;Not identified&rdquo;. DEO data is not available.</p>
    <div class="dpwh-controls"><label><span class="control-label">Infrastructure type</span><select id="infra-filter" class="facet">${options('type', state.infra, 'All infrastructure types')}</select></label><label><span class="control-label">Project region</span><select id="region-filter" class="facet">${options('region', state.region, 'All project regions')}</select></label><div class="dpwh-total"><strong>${esc(centavos(total))}</strong><span>${rows.length.toLocaleString()} schedule lines &middot; ${new Set(rows.map(row => row.saroNumber)).size} SAROs</span></div></div>
    <p class="dpwh-caption">${groupKey === 'type' ? 'Select a type to break it down by region.' : 'Select a region to see its project lines below.'} Totals follow the search, year and agency filters. Export filtered CSV includes type and region.</p>
    <div class="dpwh-groups">${[...groups].sort((a,b) => b[1].amount - a[1].amount).map(([name,item]) => `<button class="dpwh-group" type="button" data-dpwh-group="${groupKey === 'type' ? 'infra' : 'region'}" data-value="${esc(name)}"><span>${esc(name)}<small>${item.count.toLocaleString()} lines</small></span><strong>${esc(centavos(item.amount))}</strong><span class="dpwh-bar" aria-hidden="true" style="width:${item.amount / max * 100}%"></span></button>`).join('') || '<p class="muted">No matching project lines in the available schedules.</p>'}</div>`;
}

function agencyOptions() {
  const select = $('#agency-filter');
  if (state.department === 'all') {
    state.agency = 'all'; select.disabled = true;
    select.innerHTML = '<option value="all">Select a department first</option>';
    return;
  }
  const all = [...data.saros, ...data.rows];
  const values = [...new Set(all.filter((item) => (item.departmentCode || '__none__') === state.department).map((item) => item.agency).filter(Boolean))].sort((a, b) => a.localeCompare(b));
  select.innerHTML = `<option value="all">All agencies in department</option>${values.map((value) => `<option value="${esc(value)}">${esc(value)}</option>`).join('')}`;
  select.disabled = false;
  if (!values.includes(state.agency)) state.agency = 'all';
  select.value = state.agency;
}

const csvEscape = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;
function downloadCsv(filename, headings, records) {
  const csv = '\ufeff' + [headings, ...records].map((row) => row.map(csvEscape).join(',')).join('\r\n') + '\r\n';
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a'); link.href = url; link.download = filename; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function exportParticulars() {
  const headings = ['row_type', 'item_level', 'fiscal_year', 'saro_number', 'department', 'department_code', 'agency', 'date', 'purpose', 'particular', 'advice_particular', 'program_path', 'mfo_pap_code', 'object_code', 'uacs_code', 'line_amount_centavos', 'signed_saro_total_pesos', 'signed_saro_amount_stage', 'signed_saro_status_note', 'signed_saro_document_id', 'signed_saro_pdf_path', 'list_annex', 'list_page', 'list_pdf_path', 'attachment_document_id', 'source_page_pdf_path', 'advice_source_pdf_path', 'line_id', 'infra_type_from_schedule', 'region_from_schedule'];
  const rows = filteredLines().map((row) => [row.kind, row.line?.itemLevel, row.fiscalYear, row.saroNumber, row.department, row.departmentCode, row.agency, row.date, row.purpose, row.line?.description, row.line?.adviceParticular, row.line?.programPath?.join(' > '), row.line?.mfoPapCode, row.line?.objectCode, row.line?.uacsCode, row.line?.amountCentavos ?? (row.line?.amountPesos == null ? null : row.line.amountPesos * 100), row.document?.formAmountPesos ?? row.document?.amountPesos, row.document?.amountStage, row.document?.formStatusNote, row.document?.id, documentPdf(row.document), row.parent?.sourceAnnex, row.parent?.sourcePage, row.parent ? pdf(row.parent.sourceAnnex, row.parent.sourcePage) : '', row.line?.attachmentDocumentId, row.line?.sourcePdf, row.line?.adviceSourcePdf, row.line?.id, row.kind === 'project' && row.departmentCode === 'DPWH' ? DPWH.classify(row.line).type : '', row.kind === 'project' && row.departmentCode === 'DPWH' ? DPWH.classify(row.line).region : '']);
  downloadCsv(`unprogrammed-saro-records-${state.year === 'all' ? 'all-years' : state.year}-filtered.csv`, headings, rows);
}

function discrepancyHtml() {
  return `<section class="discrepancy-register" id="discrepancies" aria-labelledby="discrepancy-title"><div class="discrepancy-head"><div><div class="eyebrow">SOURCE CHECKS</div><h2 id="discrepancy-title">Documented discrepancies</h2></div></div><p>Each finding states which fields and pages were independently re-read from source images.</p><div class="discrepancy-list">${data.discrepancies.map((item) => `<details class="discrepancy-item"><summary><span class="discrepancy-annex">${esc(item.annex)}</span><span class="discrepancy-title">${esc(item.title)}</span><span class="discrepancy-kind">${esc(item.kind)}</span></summary><div class="discrepancy-body"><p>${esc(item.detail)}</p><p class="discrepancy-verification"><strong>Verification:</strong> ${esc(item.verification)}</p><div class="discrepancy-sources">${item.sources.map((source) => `<a href="${esc(source.href)}" target="_blank" rel="noopener">${esc(source.label)} ↗</a>`).join('')}</div></div></details>`).join('')}</div></section>`;
}

function render() {
  const departments = new Map([...data.saros, ...data.rows].filter((item) => item.departmentCode && item.department).map((item) => [item.departmentCode, item.department]));
  $('#main').innerHTML = `<div class="page-head"><div><div class="eyebrow">UNPROGRAMMED APPROPRIATIONS</div><h1>Special Allotment Release Orders<span class="title-acronym">&nbsp;(SAROs)</span></h1></div><div class="page-count">${data.particulars.length + data.projects.length}<small>itemized lines</small></div></div>
    <div class="control-bar"><label class="search-wrap"><span class="control-label">Search records</span><input class="search" id="search" type="search" autocomplete="off" placeholder="e.g. flood control"></label><label><span class="control-label">Year</span><select id="year-filter" class="facet"><option value="all">All years</option><option value="2024">2024</option><option value="2025">2025</option><option value="2026">2026</option></select></label><label><span class="control-label">Department</span><select id="department-filter" class="facet"><option value="all">All departments</option>${[...departments.entries()].sort((a, b) => a[1].localeCompare(b[1])).map(([code, name]) => `<option value="${esc(code)}">${esc(name)}</option>`).join('')}${[...data.saros, ...data.rows].some((item) => !item.departmentCode) ? '<option value="__none__">No department listed</option>' : ''}</select></label><label><span class="control-label">Agency</span><select id="agency-filter" class="facet"></select></label><button class="export" id="export-csv" type="button">Export filtered CSV ↓</button></div>
    <section id="dpwh-panel" class="dpwh-panel" aria-label="DPWH infrastructure drill-down"></section>
    <div class="result-summary" role="status" aria-live="polite" aria-atomic="true"><strong id="result-count"></strong><span id="result-range"></span></div>
    <div class="table-wrap"><table class="data-table table-particulars"><thead><tr>${sortHeader('saro-number', 'SARO number')}${sortHeader('department', 'Department')}${sortHeader('agency', 'Agency')}${sortHeader('purpose', 'Purpose')}${sortHeader('particular', 'Particular / codes')}${sortHeader('date', 'Date')}${sortHeader('amount', 'Line amount', 'amount')}${sortHeader('source', 'Source')}</tr></thead><tbody id="results-body"></tbody></table></div>
    <div class="table-foot"><div class="pager" id="pager"></div><a id="ebudget-download" href="data/ebudget_transactions.csv" download>eBudget listing CSV ↓</a><a id="road-fund-download" href="data/road_fund_projects.csv" download>Road-fund projects CSV ↓</a><a href="data/advice_items.csv" download>Advice requests and variances CSV ↓</a><a id="revenue-download" href="data/revenue_evidence.csv" download>Revenue evidence CSV ↓</a></div>${discrepancyHtml()}`;
  if (!['all', '2024', '2025', '2026'].includes(state.year)) state.year = 'all';
  if (state.sort === 'department' || state.sort === 'agency' || state.sort === 'saro-number') state.sort += '-asc';
  if (state.sort !== 'list' && !SORT_COLUMNS.some((column) => state.sort === `${column}-asc` || state.sort === `${column}-desc`)) state.sort = 'list';
  $('#search').value = state.query;
  $('#year-filter').value = state.year;
  if (![...$('#department-filter').options].some((option) => option.value === state.department)) state.department = 'all';
  $('#department-filter').value = state.department;
  for (const [key, field] of [['infra', 'type'], ['region', 'region']]) {
    if (state[key] !== 'all' && !data.rows.filter(DPWH.eligible).some(row => DPWH.classify(row.line)[field] === state[key])) state[key] = 'all';
  }
  agencyOptions(); renderRows();
}

$('#main').addEventListener('input', (event) => { if (event.target.id === 'search') { state.query = event.target.value; state.page = 1; renderRows(); } });
$('#main').addEventListener('change', (event) => {
  if (event.target.id === 'year-filter') state.year = event.target.value;
  if (event.target.id === 'infra-filter') state.infra = event.target.value;
  if (event.target.id === 'region-filter') state.region = event.target.value;
  if (event.target.id === 'department-filter') { state.dpwh = false; state.infra = 'all'; state.region = 'all'; state.department = event.target.value; state.agency = 'all'; agencyOptions(); }
  if (event.target.id === 'agency-filter') state.agency = event.target.value;
  state.page = 1; renderRows();
});
$('#main').addEventListener('click', (event) => {
  if (event.target.closest('#dpwh-toggle')) {
    state.dpwh = !state.dpwh; state.infra = 'all'; state.region = 'all'; state.page = 1;
    if (state.dpwh) { state.department = 'DPWH'; state.agency = 'all'; $('#department-filter').value = 'DPWH'; agencyOptions(); }
    renderRows(); return;
  }
  const group = event.target.closest('[data-dpwh-group]');
  if (group) { state[group.dataset.dpwhGroup] = group.dataset.value; state.page = 1; renderRows(); return; }
  const sortButton = event.target.closest('[data-sort]');
  if (sortButton) {
    const column = sortButton.dataset.sort;
    const direction = state.sort === `${column}-asc` ? 'desc' : state.sort === `${column}-desc` ? 'asc' : DEFAULT_SORT_DIRECTION[column] || 'asc';
    state.sort = `${column}-${direction}`;
    state.page = 1;
    renderRows();
    return;
  }
  if (event.target.id === 'export-csv') { exportParticulars(); return; }
  const pager = event.target.closest('[data-page]');
  if (pager) { state.page += pager.dataset.page === 'next' ? 1 : -1; renderRows(); document.querySelector('.table-wrap')?.scrollIntoView({ block: 'start', behavior: 'smooth' }); }
});

Promise.all([
  fetch('data/saros.json').then((response) => response.json()),
  fetch('data/documents.json').then((response) => response.json()),
  fetch('data/annexes.json').then((response) => response.json()),
  fetch('data/particulars.json').then((response) => response.json()),
  fetch('data/project_items.json').then((response) => response.json()),
  fetch('data/discrepancies.json').then((response) => response.json()),
]).then(([saros, documents, sources, particulars, projects, discrepancies]) => {
  data.saros = saros.records; data.documents = documents.records; data.sources = sources.records; data.particulars = particulars.records;
  data.projects = projects.records;
  data.discrepancies = discrepancies.records;
  data.rows = makeRows(); render();
  Promise.allSettled([
    fetch('data/ebudget_transactions.json').then((response) => response.json()),
    fetch('data/road_fund_projects.json').then((response) => response.json()),
    fetch('data/revenue_evidence.json').then((response) => response.json()),
  ]).then(([ebudget, road, revenue]) => {
    if (ebudget.status === 'fulfilled') $('#ebudget-download').textContent = `eBudget listing CSV · ${ebudget.value.records.length.toLocaleString()} transactions ↓`;
    if (road.status === 'fulfilled') $('#road-fund-download').textContent = `Road-fund projects CSV · ${road.value.records.length.toLocaleString()} rows ↓`;
    if (revenue.status === 'fulfilled') $('#revenue-download').textContent = `Revenue evidence CSV · ${revenue.value.records.length.toLocaleString()} documents ↓`;
  });
}).catch((error) => { $('#main').textContent = `Data loading error: ${error.message}`; });
