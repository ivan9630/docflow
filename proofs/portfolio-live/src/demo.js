import { auditDocuments, nextWorkflowStatus, projectMonthlyLoad, olympicsKpis } from './domain.js';

const docs = [
  { documentId: 'DMS-20481', owner: 'Atelier Nord', documentType: 'CONTRAT', updatedAt: '2026-10-04', confidence: 99 },
  { documentId: 'DMS-20482', owner: 'Équipe Projet', documentType: 'FACTURE', updatedAt: '2026-10-02', confidence: 97 },
  { documentId: 'DMS-20483', owner: '', documentType: 'EXPERTISE', updatedAt: '2026-10-01', confidence: 81 },
  { documentId: 'DMS-20484', owner: 'Cellule Qualité', documentType: 'NOTE', updatedAt: '2026-09-28', confidence: 94 },
  { documentId: 'DMS-20484', owner: 'Cellule Qualité', documentType: 'CONTRAT', updatedAt: '2026-09-28', confidence: 94 },
  { documentId: 'DMS-20486', owner: 'Atelier Sud', documentType: 'CONTRAT', updatedAt: '2026-09-26', confidence: 98 },
];
const workflowItems = [
  { id: 'EXP-042', title: 'Avis d’expertise — ligne A', owner: 'Cellule technique', status: 'submitted', history: [{ action: 'submit', status: 'submitted' }] },
  { id: 'EXP-043', title: 'Note de validation — lot B', owner: 'Pôle méthodes', status: 'changes_requested', history: [{ action: 'submit', status: 'submitted' }, { action: 'requestChanges', status: 'changes_requested' }] },
  { id: 'EXP-044', title: 'Compte-rendu — équipement C', owner: 'Équipe projet', status: 'draft', history: [] },
];
const capacity = [
  { month: 'Jan', demand: 68, capacity: 82 }, { month: 'Fév', demand: 74, capacity: 80 },
  { month: 'Mar', demand: 88, capacity: 84 }, { month: 'Avr', demand: 91, capacity: 86 },
  { month: 'Mai', demand: 78, capacity: 90 }, { month: 'Juin', demand: 95, capacity: 88 },
];
const olympicRows = [
  { athleteId:'A-01',athlete:'Lina Moreau',country:'France',event:'Aviron • double',year:2024,medal:'Gold' },
  { athleteId:'A-02',athlete:'Noah Bernard',country:'France',event:'Judo • -73 kg',year:2024,medal:'Bronze' },
  { athleteId:'A-03',athlete:'Maya Chen',country:'Canada',event:'Natation • 100 m',year:2024,medal:'Silver' },
  { athleteId:'A-04',athlete:'Eli Turner',country:'Canada',event:'Athlétisme • relais',year:2020,medal:'Gold' },
  { athleteId:'A-05',athlete:'Aya Diallo',country:'Sénégal',event:'Escrime • sabre',year:2024,medal:'Bronze' },
  { athleteId:'A-06',athlete:'Iris Novak',country:'France',event:'Cyclisme • piste',year:2020,medal:'Silver' },
  { athleteId:'A-07',athlete:'Theo Silva',country:'Brésil',event:'Skate • street',year:2024,medal:'Gold' },
  { athleteId:'A-08',athlete:'Mina Park',country:'Corée',event:'Tir à l’arc',year:2024,medal:'Silver' },
  { athleteId:'A-09',athlete:'Sam Okafor',country:'Nigéria',event:'Athlétisme • 200 m',year:2020,medal:'Bronze' },
  { athleteId:'A-09',athlete:'Sam Okafor',country:'Nigéria',event:'Athlétisme • 200 m',year:2020,medal:'Bronze' },
];

const state = { view: 'migration', workflowItems, audit: [], capacityResult: [], olympics: null };
const panel = document.querySelector('#panel');
const views = {
  migration: { number: '01', title: 'Reprise documentaire & contrôles de qualité', desc: 'Un lot synthétique de documents est contrôlé avant migration : identifiants uniques, propriétaires, typologie cible et format de date. Le résultat sépare les dossiers prêts des exceptions à instruire.', button: 'Rejouer le contrôle' },
  workflow: { number: '02', title: 'Circuit de validation d’une expertise', desc: 'Parcours métier minimal : brouillon → soumis → approuvé, avec retour possible pour correction. Les transitions invalides sont refusées et l’historique reste visible.', button: 'Réinitialiser le workflow' },
  capacity: { number: '03', title: 'Lecture de charge & capacité', desc: 'Des prévisions fictives de demande sont comparées à une capacité mensuelle. Les écarts aident à repérer les périodes sous tension ; ce calcul illustratif n’est pas un modèle prédictif entraîné.', button: 'Recalculer les indicateurs' },
  olympics: { number: '04', title: 'Pipeline analytique — médailles sportives', desc: 'Un micro-lot synthétique passe par validation, déduplication et agrégation SQL-like. Les KPI et rejets sont recalculés dans le navigateur ; aucune donnée officielle de résultats n’est utilisée.', button: 'Exécuter le pipeline' },
};
const badge = (status) => status === 'Conforme' || status === 'approved' ? '<span class="badge ok">Conforme</span>' : status === 'À corriger' || status === 'changes_requested' ? '<span class="badge error">À corriger</span>' : status === 'submitted' ? '<span class="badge review">En revue</span>' : '<span class="badge review">Brouillon</span>';
const metric = (label, value, sub = '', color = '') => `<div class="metric ${color}"><div class="metric-label">${label}</div><div class="metric-value">${value}</div><div class="metric-sub">${sub}</div></div>`;

function migrationView() {
  const rows = state.audit.length ? state.audit : auditDocuments(docs);
  const ok = rows.filter((r) => r.status === 'Conforme').length;
  const issueCount = rows.length - ok;
  return `<div class="metrics">${metric('Lot contrôlé', rows.length, 'lignes synthétiques')}${metric('Prêts à migrer', ok, 'tous les contrôles passent', 'good')}${metric('Exceptions', issueCount, 'à qualifier avant reprise', issueCount ? 'warn' : 'good')}${metric('Taux de conformité', `${Math.round(ok / rows.length * 100)}%`, 'sur cet échantillon', issueCount ? 'warn' : 'good')}</div>
  <div class="grid"><article class="card"><h3 class="card-title">Échantillon de contrôle <small>règles versionnées · v1</small></h3><div style="overflow:auto"><table><thead><tr><th>ID source</th><th>Propriétaire</th><th>Type cible</th><th>Contrôle</th><th>Anomalie</th></tr></thead><tbody>${rows.map((r) => `<tr><td class="mono">${r.documentId || '—'}</td><td>${r.owner || '—'}</td><td><span class="code-chip">${r.documentType}</span></td><td>${badge(r.status)}</td><td>${r.issues.join(' · ') || '—'}</td></tr>`).join('')}</tbody></table></div></article>
  <article class="card"><h3 class="card-title">Chaîne de reprise <small>simulation locale</small></h3><div class="timeline">${[['1','Extraire','CSV de démonstration reçu'],['2','Normaliser','Schéma cible et valeurs contrôlés'],['3','Qualifier','Anomalies regroupées pour revue'],['4','Exporter','Uniquement les lignes conformes']].map(([n,t,s],i)=>`<div class="step"><span class="step-dot ${i<3?'':'pending'}">${i<3?'✓':n}</span><div class="step-copy"><strong>${t}</strong><span>${s}</span></div></div>`).join('')}</div><p class="insight">Les règles bloquent un identifiant dupliqué, un propriétaire vide et une typologie inconnue avant l’export.</p></article></div>`;
}
function workflowView() {
 const items=state.workflowItems;
 const submitted=items.filter(x=>x.status==='submitted').length, approved=items.filter(x=>x.status==='approved').length, changes=items.filter(x=>x.status==='changes_requested').length;
 return `<div class="metrics">${metric('Dossiers',items.length,'file de démonstration')}${metric('En revue',submitted,'attendent une décision','warn')}${metric('Approuvés',approved,'décision tracée','good')}${metric('À reprendre',changes,'retour explicite','bad')}</div><div class="grid"><article class="card"><h3 class="card-title">File des avis d’expertise <small>actions interactives</small></h3><div style="overflow:auto"><table><thead><tr><th>Référence</th><th>Objet</th><th>Responsable</th><th>État</th><th>Action</th></tr></thead><tbody>${items.map(x=>`<tr><td class="mono">${x.id}</td><td>${x.title}</td><td>${x.owner}</td><td>${badge(x.status)}</td><td>${x.status==='submitted'?`<button class="code-chip action" data-id="${x.id}" data-action="approve">Valider</button> <button class="code-chip action" data-id="${x.id}" data-action="requestChanges">Retourner</button>`:x.status==='changes_requested'?`<button class="code-chip action" data-id="${x.id}" data-action="resubmit">Resoumettre</button>`:`<button class="code-chip action" data-id="${x.id}" data-action="submit">Soumettre</button>`}</td></tr>`).join('')}</tbody></table></div></article><article class="card"><h3 class="card-title">Historique d’un dossier <small>${items[0].id}</small></h3><div class="timeline">${(items[0].history.length?items[0].history:[{action:'created',status:'draft'}]).map((h,i)=>`<div class="step"><span class="step-dot">${i+1}</span><div class="step-copy"><strong>${h.action==='submit'?'Soumis pour validation':h.action==='approve'?'Approuvé':h.action==='requestChanges'?'Corrections demandées':h.action==='resubmit'?'Nouvelle version soumise':'Créé'}</strong><span>État : ${h.status}</span></div></div>`).join('')}</div><p class="insight">La règle métier interdit l’approbation d’un brouillon. Les actions modifient uniquement l’état en mémoire du navigateur.</p></article></div>`;
}
function capacityView() {
 const data=state.capacityResult.length?state.capacityResult:projectMonthlyLoad(capacity);
 const max=Math.max(...data.flatMap(x=>[x.demand,x.capacity]));
 return `<div class="metrics">${metric('Mois en tension',data.filter(x=>x.gap>0).length,'demande > capacité',data.some(x=>x.gap>0)?'warn':'good')}${metric('Pic de demande',`${Math.max(...data.map(x=>x.demand))} j`, 'jours fictifs')}${metric('Marge moyenne',`${Math.round(data.reduce((s,x)=>s+x.gap,0)/data.length)} j`,'capacité moins charge',data.reduce((s,x)=>s+x.gap,0)<0?'bad':'good')}${metric('Période',`${data.length} mois`,'projection illustrative')}</div><div class="grid"><article class="card"><h3 class="card-title">Demande vs capacité <small>jours de charge par mois</small></h3><div class="bars">${data.map(x=>`<div class="bar-row"><span>${x.month} · charge</span><div class="bar-track"><div class="bar-fill ${x.gap>0?'amber':''}" style="width:${x.demand/max*100}%"></div></div><span class="bar-value">${x.demand}</span></div><div class="bar-row" style="margin-top:-8px"><span style="color:#70819a">Capacité équipe</span><div class="bar-track"><div class="bar-fill green" style="width:${x.capacity/max*100}%"></div></div><span class="bar-value">${x.capacity}</span></div>`).join('')}</div><p class="insight">Écart cumulé : ${data.reduce((s,x)=>s+x.gap,0)} jours. Ajuster la capacité, le périmètre ou le calendrier avant de conclure à une surcharge.</p></article><article class="card"><h3 class="card-title">Lecture managériale <small>exemple de décision</small></h3><div class="timeline">${data.filter(x=>x.gap>0).map((x,i)=>`<div class="step"><span class="step-dot pending">!</span><div class="step-copy"><strong>${x.month} — déficit estimé ${x.gap} j</strong><span>Examiner dépendances et disponibilité avant arbitrage.</span></div></div>`).join('')||'<div class="empty-state">Pas de dépassement dans ce scénario.</div>'}</div><p class="insight">Aucune IA ni prédiction n’est revendiquée : les résultats proviennent d’une formule déterministe documentée.</p></article></div>`;
}
function olympicsView() {
 const data=state.olympics??olympicsKpis(olympicRows);
 const max=Math.max(...data.countries.map(x=>x.medals));
 return `<div class="metrics">${metric('Lignes valides',data.valid.length,'après validation', 'good')}${metric('Lignes rejetées',data.rejected.length,'erreur ou doublon',data.rejected.length?'warn':'good')}${metric('Athlètes distincts',data.uniqueAthletes,'identifiant de démonstration')}${metric('Médailles',data.totalMedals,`${data.years} éditions fictives`)}</div><div class="grid"><article class="card"><h3 class="card-title">Médailles par pays <small>agrégation du lot</small></h3><div class="bars">${data.countries.map(x=>`<div class="bar-row"><span>${x.country}</span><div class="bar-track"><div class="bar-fill" style="width:${x.medals/max*100}%"></div></div><span class="bar-value">${x.medals}</span></div>`).join('')}</div><p class="insight">Étapes : validation du schéma → déduplication (athlète, épreuve, année) → agrégation par pays. Un export CSV peut être ajouté à partir des lignes validées.</p></article><article class="card"><h3 class="card-title">Lignes mises en quarantaine <small>motif de rejet</small></h3><table><thead><tr><th>Athlète</th><th>Épreuve</th><th>Motif</th></tr></thead><tbody>${data.rejected.map(r=>`<tr><td>${r.athlete}</td><td>${r.event}</td><td>${r.athleteId=== 'A-09'?'Doublon de clé métier':'Schéma invalide'}</td></tr>`).join('')||'<tr><td colspan="3">Aucun rejet.</td></tr>'}</tbody></table><p class="insight">Le jeu est volontairement réduit et inventé : aucun chiffre ne décrit les vrais Jeux Olympiques.</p></article></div>`;
}
const renderers={migration:migrationView,workflow:workflowView,capacity:capacityView,olympics:olympicsView};
function render(){const v=views[state.view];panel.innerHTML=`<div class="panel-head"><div><div class="project-kicker">DÉMONSTRATEUR ${v.number}</div><h2>${v.title}</h2><p>${v.desc}</p></div><button class="run-button" id="run">${v.button} <span aria-hidden="true">↗</span></button></div>${renderers[state.view]()}`;
 panel.querySelector('#run').addEventListener('click',()=>{if(state.view==='migration')state.audit=auditDocuments([...docs]);if(state.view==='workflow')state.workflowItems=workflowItems.map(x=>({...x,history:[...x.history]}));if(state.view==='capacity')state.capacityResult=projectMonthlyLoad(capacity);if(state.view==='olympics')state.olympics=olympicsKpis(olympicRows);render();});
 panel.querySelectorAll('.action').forEach(btn=>btn.addEventListener('click',()=>{try{const i=state.workflowItems.findIndex(x=>x.id===btn.dataset.id);state.workflowItems[i]=nextWorkflowStatus(state.workflowItems[i],btn.dataset.action);render();}catch(e){panel.insertAdjacentHTML('afterbegin',`<div class="error-banner" role="alert">${e.message}</div>`);}}));}
document.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>{state.view=tab.dataset.view;document.querySelectorAll('.tab').forEach(t=>{const active=t===tab;t.classList.toggle('active',active);t.setAttribute('aria-selected',String(active));});render();}));
render();
