import test from 'node:test';
import assert from 'node:assert/strict';
import { auditDocuments, nextWorkflowStatus, projectMonthlyLoad, olympicsKpis } from '../src/domain.js';

test('document audit identifies missing fields, unknown type and duplicate ids',()=>{
 const out=auditDocuments([
  {documentId:'1',owner:'A',documentType:'CONTRAT',updatedAt:'2026-01-01'},
  {documentId:'2',owner:'',documentType:'NOTE',updatedAt:'bad'},
  {documentId:'1',owner:'B',documentType:'FACTURE',updatedAt:'2026-01-01'},
 ]);
 assert.equal(out[0].status,'Conforme');
 assert.deepEqual(out[1].issues,['Propriétaire absent','Type non reconnu','Date invalide']);
 assert.ok(out[2].issues.includes('Identifiant dupliqué'));
});
test('workflow allows legal transitions and rejects illegal transition',()=>{
 const item={status:'submitted',history:[]};
 assert.equal(nextWorkflowStatus(item,'approve').status,'approved');
 assert.throws(()=>nextWorkflowStatus(item,'submit'),/impossible/);
});
test('capacity projection handles zero and invalid capacity',()=>{
 assert.equal(projectMonthlyLoad([{month:'Jan',demand:3,capacity:0}])[0].utilization,null);
 assert.throws(()=>projectMonthlyLoad([{month:'Jan',demand:-2,capacity:3}]),/nombres positifs/);
});
test('Olympics pipeline deduplicates and rejects invalid rows',()=>{
 const rows=[
  {athleteId:'a',event:'100 m',year:2024,medal:'Gold',country:'X'},
  {athleteId:'a',event:'100 m',year:2024,medal:'Gold',country:'X'},
  {athleteId:'b',event:'saut',year:1880,medal:'Silver',country:'Y'},
 ];
 const result=olympicsKpis(rows);
 assert.equal(result.valid.length,1);assert.equal(result.rejected.length,2);assert.equal(result.uniqueAthletes,1);
});
