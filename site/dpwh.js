/* Schedule headings are evidence of project type/location, not implementing DEO. */
const DPWH = {
  classify(line) {
    const path = line.programPath || [];
    const heading = path.join(' ');
    let type = 'Not identified';
    if (/right[ -]*of[ -]*way/i.test(heading)) type = 'Right-of-way claims';
    else {
      for (const text of [...path].reverse()) {
        if (/organizational outcome/i.test(text)) continue;
        if (/flood|drainage/i.test(text)) { type = 'Flood control and drainage'; break; }
        if (/water supply|septage|sewerage|rain water/i.test(text)) { type = 'Water supply and sanitation'; break; }
        if (/roads? and\/or bridges|roads and bridges/i.test(text)) { type = 'Roads and bridges (combined)'; break; }
        if (/bridges?|bridge program/i.test(text)) { type = 'Bridges'; break; }
        if (/road networks/i.test(text)) { type = 'Road networks (unspecified)'; break; }
        if (/roads?|causeway|carriageway/i.test(text)) { type = 'Roads'; break; }
        if (/buildings?|multipurpose|multi-purpose|evacuation|health facilities/i.test(text)) { type = 'Buildings and public facilities'; break; }
        if (/national security/i.test(text)) { type = 'National security infrastructure (mixed)'; break; }
      }
    }
    let region = 'Not identified';
    for (const text of path) {
      const value = text.trim().replace(/\s*\(Attachment [^)]+\)$/i, '');
      if (/^(National Capital Region|NCR)$/i.test(value)) region = 'National Capital Region';
      else if (/^(Cordillera Administrative Region|CAR)$/i.test(value)) region = 'Cordillera Administrative Region';
      else if (/^(?:Region\s+)?(I|II|III|IV-A|IV-B|V|VI|VII|VIII|IX|X|XI|XII|XIII)$/i.test(value)) region = `Region ${value.replace(/^Region\s+/i, '').toUpperCase()}`;
    }
    return { type, region };
  },
  eligible(row) {
    return row.kind === 'project' && row.departmentCode === 'DPWH' && row.line.itemLevel !== 'regional_summary' && row.document?.amountStage === 'released';
  },
};
