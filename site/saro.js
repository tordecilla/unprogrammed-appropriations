const $ = (selector) => document.querySelector(selector);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
const pesos = (number) => number == null ? '—' : `₱${new Intl.NumberFormat('en-PH', { maximumFractionDigits: 0 }).format(number)}`;
const centavos = (number) => number == null ? '—' : `₱${new Intl.NumberFormat('en-PH', { minimumFractionDigits: number % 100 ? 2 : 0, maximumFractionDigits: 2 }).format(number / 100)}`;
const id = new URLSearchParams(location.search).get('id');
const returnQuery = new URLSearchParams(location.search).get('from') || '';
const returnHref = returnQuery.startsWith('?') && !returnQuery.includes('#') ? `./${returnQuery}` : './';
const tableTools = (key, label, count) => `<div class="detail-table-tools"><label><span class="control-label">Search ${label}</span><input class="search" type="search" data-table-search="${key}" placeholder="Filter ${label}" autocomplete="off"></label><span class="detail-table-count" data-table-count="${key}" role="status">${count.toLocaleString()} ${count === 1 ? 'row' : 'rows'}</span><button class="export" type="button" data-table-export="${key}">Export filtered CSV ↓</button></div>`;
const csvEscape = (value) => `"${String(value ?? '').replaceAll('"', '""')}"`;
function downloadCsv(filename, headings, records) {
  const content = '\ufeff' + [headings, ...records].map((row) => row.map(csvEscape).join(',')).join('\r\n') + '\r\n';
  const url = URL.createObjectURL(new Blob([content], { type: 'text/csv;charset=utf-8' }));
  const link = document.createElement('a'); link.href = url; link.download = filename; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

Promise.all([
  fetch('data/documents.json').then((response) => response.json()),
  fetch('data/saros.json').then((response) => response.json()),
  fetch('data/particulars.json').then((response) => response.json()),
  fetch('data/project_items.json').then((response) => response.json()),
  fetch('data/annexes.json').then((response) => response.json()),
  fetch('data/status_rows.json').then((response) => response.json()),
  fetch('data/status_allocations.json').then((response) => response.json()),
  fetch('data/ebudget_transactions.json').then((response) => response.json()),
  fetch('data/document_components.json').then((response) => response.json()),
]).then(([documentsJson, sarosJson, particularsJson, projectsJson, annexesJson, statusRowsJson, statusAllocationsJson, listingsJson, componentsJson]) => {
  const documents = documentsJson.records;
  $('.header-download').href = returnHref;
  const order = documents.find((item) => item.id === id && item.type === 'SARO');
  if (!order) { $('#detail').innerHTML = `<a class="back" href="${esc(returnHref)}">← All particulars</a><h1>SARO not found</h1>`; return; }
  const parent = sarosJson.records.find((item) => item.orderDocumentId === id);
  const candidate = parent ? null : sarosJson.records.find((item) => (item.candidateOrderDocumentIds || []).includes(id));
  const list = parent || candidate;
  const lines = particularsJson.records.filter((item) => item.documentId === id);
  const projects = projectsJson.records.filter((item) => item.signedDocumentId === id);
  const statusRows = statusRowsJson.records.filter((item) => (list && item.purposeListId === list.id) || item.saroNumber === order.saroNumber);
  const statusIds = new Set(statusRows.map((item) => item.id));
  const statusAllocations = statusAllocationsJson.records.filter((item) => statusIds.has(item.statusRowId));
  const listingRows = listingsJson.records.filter((item) => item.signedDocumentId === id || (order.saroNumber && item.saroNumber === order.saroNumber));
  const componentRows = componentsJson.records.filter((item) => order.saroNumber && item.relatedSaroNumber === order.saroNumber);
  const source = annexesJson.records.find((item) => item.id === `annex-${order.annexId.toLowerCase()}`);
  const originalUrl = source ? `${source.releaseUrl || `../court-documents/${encodeURIComponent(source.file)}`}#page=${order.pageStart}` : '#';
  const listSource = list && annexesJson.records.find((item) => item.id === `annex-${list.sourceAnnex.toLowerCase()}`);
  const listUrl = listSource ? `${listSource.releaseUrl || `../court-documents/${encodeURIComponent(listSource.file)}`}#page=${list.sourcePage}` : '';
  const related = (parent?.relatedDocumentIds || []).map((relatedId) => documents.find((item) => item.id === relatedId)).filter(Boolean);
  const adviceDocuments = documents.filter((item) => item.relatedIds?.includes(id) && item.type !== 'SARO' && !related.some((relatedItem) => relatedItem.id === item.id));
  const projectAttachments = [...new Set(projects.map((item) => item.attachmentDocumentId))].map((attachmentId) => documents.find((item) => item.id === attachmentId)).filter((item) => item && !related.some((relatedItem) => relatedItem.id === item.id));
  const total = order.formAmountPesos ?? order.amountPesos;
  const department = list?.department || order.formDepartment || order.agency;
  const agency = list?.agency || order.formAgency;
  const sourceLinks = [
    `<a href="${esc(order.standalonePdf || originalUrl)}" target="_blank" rel="noopener">Signed SARO PDF ↗</a>`,
    `<a href="${esc(originalUrl)}" target="_blank" rel="noopener">Original Annex ${esc(order.annexId)} · PDF pp. ${order.pageStart}${order.pageEnd > order.pageStart ? `–${order.pageEnd}` : ''} ↗</a>`,
    ...(order.statusEvidence || []).map((item) => `<a href="${esc(item.sourcePdf)}" target="_blank" rel="noopener">${esc(item.label)} · Annex ${esc(order.annexId)} p. ${item.sourcePage} ↗</a>`),
    listUrl ? `<a href="${esc(listUrl)}" target="_blank" rel="noopener">Purpose list · Annex ${esc(list.sourceAnnex)} p. ${list.sourcePage} ↗</a>` : '',
    ...related.map((item) => `<a href="${esc(item.standalonePdf || '#')}" target="_blank" rel="noopener">${esc(item.type)} · Annex ${esc(item.annexId)} pp. ${item.pageStart}${item.pageEnd > item.pageStart ? `–${item.pageEnd}` : ''}${item.duplicateOf ? ' · duplicate copy' : ''} ↗</a>`),
    ...adviceDocuments.map((item) => `<a href="${esc(item.standalonePdf || '#')}" target="_blank" rel="noopener">${esc(item.type)} · Annex ${esc(item.annexId)} pp. ${item.pageStart}${item.pageEnd > item.pageStart ? `–${item.pageEnd}` : ''}${item.duplicateOf ? ' · duplicate copy' : ''} ↗</a>`),
    ...projectAttachments.map((item) => `<a href="${esc(item.standalonePdf || '#')}" target="_blank" rel="noopener">${esc(item.type)} · Annex ${esc(item.annexId)} pp. ${item.pageStart}${item.pageEnd > item.pageStart ? `–${item.pageEnd}` : ''} ↗</a>`),
    ...[...new Map(statusRows.flatMap((item) => item.sourcePages.map((page, index) => [`${item.sourceAnnex}-${page}`, { annex: item.sourceAnnex, page, href: item.sourcePagePdfs?.[index] }]))).values()].map((item) => `<a href="${esc(item.href || '#')}" target="_blank" rel="noopener">Status report · Annex ${esc(item.annex)} p. ${item.page} ↗</a>`),
    ...[...new Map(listingRows.map((item) => [`${item.sourceAnnex}-${item.sourcePage}`, item])).values()].map((item) => `<a href="${esc(item.sourcePdf)}" target="_blank" rel="noopener">eBudget listing · Annex ${esc(item.sourceAnnex)} p. ${item.sourcePage} ↗</a>`),
  ].filter(Boolean);
  const fields = [
    ['Department', department], ['Agency', agency], ['Operating unit', order.formOperatingUnit], ['Locality', order.formLocality],
    ['Issue date', order.date || list?.date], ['Valid for obligation until', order.validUntil], ['Organization code', order.formOrgCode],
    ['Funding source', order.fundingSource], ['Funding source code', order.fundingSourceCode],
  ];
  const lineRows = lines.map((line) => `<tr><td class="mono">${line.lineNumber}</td><td><strong>${esc(line.description || '—')}</strong>${line.adviceParticular ? `<small>Advice detail: ${esc(line.adviceParticular)} · <a href="${esc(line.adviceSourcePdf)}" target="_blank" rel="noopener">Annex B p.${line.adviceSourcePage} ↗</a></small>` : ''}${line.programPath?.length ? `<small>${esc(line.programPath.join(' › '))}</small>` : ''}</td><td class="mono">${esc(line.mfoPapCode || '—')}</td><td class="mono">${esc(line.objectCode || '—')}</td><td class="amount">${esc(pesos(line.amountPesos))}</td></tr>`).join('');
  const projectRows = projects.map((line) => `<tr id="project-${esc(line.id)}"><td class="mono">${esc(line.lineNumber || '—')}</td><td>${esc(line.description)}${line.programPath?.length ? `<small>${esc(line.programPath.join(' › '))}</small>` : ''}</td><td class="mono">${esc(line.uacsCode || '—')}</td><td class="amount">${esc(centavos(line.amountCentavos))}</td><td><a class="page-link" href="${esc(line.sourcePdf)}" target="_blank" rel="noopener">Annex ${esc(line.sourceAnnex)} p.${line.sourcePage} ↗</a></td></tr>`).join('');
  const projectsHtml = projects.length ? `<h2>Attached schedule lines <span>${projects.length} line${projects.length === 1 ? '' : 's'}</span></h2>${tableTools('schedule', 'schedule lines', projects.length)}<div class="table-wrap"><table class="data-table detail-particulars project-detail-table" data-detail-table="schedule"><thead><tr><th>#</th><th>Project, claim, or visible summary / program path</th><th>UACS code</th><th class="amount">Amount</th><th>Source</th></tr></thead><tbody>${projectRows}</tbody></table></div>` : '';
  const statusSource = (cell) => { const annex = annexesJson.records.find((item) => item.id === `annex-${cell.sourceAnnex.toLowerCase()}`); return cell.standalonePdf || (annex ? `${annex.releaseUrl || `../court-documents/${encodeURIComponent(annex.file)}`}#page=${cell.sourcePage}` : ''); };
  const statusHtml = statusRows.length ? `<h2>UA status report <span>${statusAllocations.length} allocation cell${statusAllocations.length === 1 ? '' : 's'}</span></h2>${tableTools('status', 'status allocations', statusAllocations.length)}<div class="table-wrap"><table class="data-table detail-particulars status-table" data-detail-table="status"><thead><tr><th>Category</th><th>Expense class</th><th>Amount</th><th>Source</th></tr></thead><tbody>${statusAllocations.map((cell) => `<tr><td>${esc(cell.category || '—')}</td><td class="mono">${esc(cell.expenseClass || '—')}</td><td class="amount">${esc(pesos(cell.amountPesos))}</td><td><a class="page-link" href="${esc(statusSource(cell) || '#')}" target="_blank" rel="noopener">Annex ${esc(cell.sourceAnnex)} p.${cell.sourcePage} ↗</a></td></tr>`).join('') || '<tr><td colspan="4" class="empty">No allocation cells available.</td></tr>'}</tbody></table></div>` : '';
  const listingHtml = listingRows.length ? `<h2>eBudget SARO listing <span>${listingRows.length} transaction${listingRows.length === 1 ? '' : 's'}</span></h2><div class="table-wrap"><table class="data-table detail-particulars"><thead><tr><th>Issue date</th><th>Purpose shown</th><th>Funding source</th><th class="amount">Listing total</th><th>Source</th></tr></thead><tbody>${listingRows.map((item) => `<tr><td class="mono">${esc(item.issueDate || '—')}</td><td>${esc(item.purpose || '—')}</td><td class="mono">${esc(item.fundingSourceCode)}</td><td class="amount">${esc(centavos(item.totalCentavos))}</td><td><a class="page-link" href="${esc(item.sourcePdf)}" target="_blank" rel="noopener">Annex ${esc(item.sourceAnnex)} p.${item.sourcePage} ↗</a></td></tr>`).join('')}</tbody></table></div>` : '';
  const componentHtml = componentRows.length ? `<h2>Advice document components <span>${componentRows.length} cell${componentRows.length === 1 ? '' : 's'}</span></h2><div class="table-wrap"><table class="data-table detail-particulars"><thead><tr><th>Component</th><th>Type</th><th class="amount">Amount</th><th>Source</th></tr></thead><tbody>${componentRows.map((item) => `<tr><td>${esc(item.description)}</td><td class="mono">${esc(item.amountType)}</td><td class="amount">${esc(centavos(item.amountCentavos))}</td><td><a class="page-link" href="${esc(item.sourcePdf)}" target="_blank" rel="noopener">Annex ${esc(item.sourceAnnex)} p.${item.sourcePage} ↗</a></td></tr>`).join('')}</tbody></table></div>` : '';
  $('#detail').innerHTML = `<a class="back" href="${esc(returnHref)}">← All particulars</a>
    <div class="detail-head"><div><div class="eyebrow">SIGNED SPECIAL ALLOTMENT RELEASE ORDER · FY ${esc(list?.fiscalYear || order.date?.slice(0, 4) || '')}</div><h1>${esc(order.saroNumber || 'SARO')}</h1><p class="detail-id">${esc(department || '—')} · ${esc(agency || '—')}</p></div><div class="large-amount">${esc(pesos(total))}<small>${order.amountStage === 'status_unresolved' ? 'Form total · status unresolved' : 'SARO total'}</small></div></div>
    ${candidate ? `<div class="match-note">${esc(candidate.candidateOrderNote || 'The purpose list and signed form appear related, but their SARO numbers differ or the signed number is partly obscured. Compare both source PDFs before treating this as an exact match.')}</div>` : ''}
    ${order.formStatusNote ? `<div class="match-note">${esc(order.formStatusNote)}</div>` : ''}
    ${order.missingAttachmentNote ? `<div class="match-note">${esc(order.missingAttachmentNote)}</div>` : ''}
    <div class="saro-detail-grid"><section class="saro-detail-main"><h2>Purpose</h2><dl class="purpose-fields">${list?.purpose ? `<div><dt>Purpose list</dt><dd>${esc(list.purpose)}</dd></div>` : ''}${order.formPurpose ? `<div><dt>Signed SARO</dt><dd>${esc(order.formPurpose)}</dd></div>` : ''}</dl>
      <h2>Particulars <span>${lines.length} line${lines.length === 1 ? '' : 's'}</span></h2>${tableTools('particulars', 'particulars', lines.length)}<div class="table-wrap"><table class="data-table detail-particulars" data-detail-table="particulars"><thead><tr><th>#</th><th>Particular / program path</th><th>MFO/PAP code</th><th>Object code</th><th class="amount">Line amount</th></tr></thead><tbody>${lineRows || '<tr><td colspan="5" class="empty">No particulars available.</td></tr>'}</tbody></table></div>
      ${projectsHtml}${statusHtml}${listingHtml}${componentHtml}<h2>Form fields</h2><dl class="detail-fields">${fields.map(([label, value]) => `<div><dt>${esc(label)}</dt><dd>${esc(value || '—')}</dd></div>`).join('')}</dl></section>
      <aside class="saro-source-panel"><h2>Source documents</h2><div class="source-stack">${sourceLinks.join('')}</div></aside></div>`;
  const tables = {
    particulars: {
      items: lines,
      headings: ['saro_number', 'line_number', 'particular', 'advice_particular', 'program_path', 'mfo_pap_code', 'object_code', 'amount_pesos', 'signed_saro_pdf'],
      row: (line) => [order.saroNumber, line.lineNumber, line.description, line.adviceParticular, line.programPath?.join(' > '), line.mfoPapCode, line.objectCode, line.amountPesos, order.standalonePdf || originalUrl],
    },
    schedule: {
      items: projects,
      headings: ['saro_number', 'line_number', 'description', 'program_path', 'uacs_code', 'amount_centavos', 'source_annex', 'source_page', 'source_pdf'],
      row: (line) => [order.saroNumber, line.lineNumber, line.description, line.programPath?.join(' > '), line.uacsCode, line.amountCentavos, line.sourceAnnex, line.sourcePage, line.sourcePdf],
    },
    status: {
      items: statusAllocations,
      headings: ['saro_number', 'category', 'expense_class', 'amount_pesos', 'source_annex', 'source_page', 'source_pdf'],
      row: (cell) => [order.saroNumber, cell.category, cell.expenseClass, cell.amountPesos, cell.sourceAnnex, cell.sourcePage, statusSource(cell)],
    },
  };
  for (const [key, config] of Object.entries(tables)) {
    const table = document.querySelector(`[data-detail-table="${key}"]`);
    if (!table) continue;
    const rows = [...table.tBodies[0].rows].slice(0, config.items.length);
    const input = document.querySelector(`[data-table-search="${key}"]`);
    const count = document.querySelector(`[data-table-count="${key}"]`);
    const empty = document.createElement('tr');
    empty.className = 'filter-empty';
    empty.innerHTML = `<td colspan="${table.tHead.rows[0].cells.length}" class="empty">No matching rows.</td>`;
    empty.hidden = true;
    table.tBodies[0].append(empty);
    input.addEventListener('input', () => {
      const query = input.value.trim().toLocaleLowerCase();
      let visible = 0;
      rows.forEach((row) => { row.hidden = !row.textContent.toLocaleLowerCase().includes(query); if (!row.hidden) visible++; });
      empty.hidden = visible !== 0 || config.items.length === 0;
      count.textContent = `${visible.toLocaleString()} of ${config.items.length.toLocaleString()} ${config.items.length === 1 ? 'row' : 'rows'}`;
    });
    document.querySelector(`[data-table-export="${key}"]`).addEventListener('click', () => {
      const visibleRows = config.items.filter((_, index) => !rows[index].hidden).map(config.row);
      downloadCsv(`${String(order.saroNumber || id).replace(/[^a-z0-9-]/gi, '-')}-${key}.csv`, config.headings, visibleRows);
    });
  }
  document.title = `${order.saroNumber || 'SARO'} — Unprogrammed Appropriations`;
  if (location.hash.startsWith('#project-')) document.getElementById(decodeURIComponent(location.hash.slice(1)))?.scrollIntoView({ block: 'center' });
}).catch((error) => { $('#detail').textContent = `Data loading error: ${error.message}`; });
