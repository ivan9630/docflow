// Toutes les fonctions métier sont pures et prennent des cas synthétiques.
export function auditDocuments(rows) {
  const seen = new Set();
  return rows.map((row) => {
    const issues = [];
    if (!row.documentId) issues.push('Identifiant absent');
    if (row.documentId && seen.has(row.documentId)) issues.push('Identifiant dupliqué');
    if (row.documentId) seen.add(row.documentId);
    if (!row.owner?.trim()) issues.push('Propriétaire absent');
    if (!['CONTRAT', 'FACTURE', 'EXPERTISE'].includes(row.documentType)) issues.push('Type non reconnu');
    if (!/^\d{4}-\d{2}-\d{2}$/.test(row.updatedAt ?? '')) issues.push('Date invalide');
    return { ...row, issues, status: issues.length ? 'À corriger' : 'Conforme' };
  });
}

export function nextWorkflowStatus(item, action) {
  const transitions = {
    submit: { draft: 'submitted' },
    approve: { submitted: 'approved' },
    requestChanges: { submitted: 'changes_requested' },
    resubmit: { changes_requested: 'submitted' },
  };
  const next = transitions[action]?.[item.status];
  if (!next) throw new Error(`Transition ${action} impossible depuis ${item.status}`);
  return { ...item, status: next, history: [...(item.history ?? []), { action, status: next }] };
}

export function projectMonthlyLoad(months) {
  if (!Array.isArray(months) || months.length === 0) throw new Error('Au moins un mois est requis');
  return months.map((m) => {
    const demand = Number(m.demand);
    const capacity = Number(m.capacity);
    if (!Number.isFinite(demand) || !Number.isFinite(capacity) || demand < 0 || capacity < 0) {
      throw new Error('Charge et capacité doivent être des nombres positifs ou nuls');
    }
    return { month: m.month, demand, capacity, utilization: capacity === 0 ? null : Math.round((demand / capacity) * 100), gap: demand - capacity };
  });
}

export function olympicsKpis(rows) {
  const keys = new Set();
  const valid = [];
  const rejected = [];
  for (const row of rows) {
    const key = `${row.athleteId}:${row.event}:${row.year}`;
    const year = Number(row.year);
    const medal = ['Gold', 'Silver', 'Bronze'].includes(row.medal);
    const bad = !row.athleteId || !row.event || !Number.isInteger(year) || year < 1896 || year > 2024 || !medal || keys.has(key);
    if (bad) { rejected.push(row); continue; }
    keys.add(key);
    valid.push({ ...row, year });
  }
  const byCountry = Object.groupBy ? Object.groupBy(valid, (r) => r.country) : valid.reduce((acc, r) => ((acc[r.country] ??= []).push(r), acc), {});
  return { valid, rejected, totalMedals: valid.length, uniqueAthletes: new Set(valid.map((r) => r.athleteId)).size,
    years: new Set(valid.map((r) => r.year)).size,
    countries: Object.entries(byCountry).map(([country, medals]) => ({ country, medals: medals.length })).sort((a, b) => b.medals - a.medals) };
}
