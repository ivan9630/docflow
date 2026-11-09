const {test}=require('node:test'),assert=require('node:assert/strict'),{simulate}=require('../engine');
const base={hours:72,capacity:80,power:25,efficiency:.9,h2Capacity:120,h2Power:15,h2Efficiency:.48,initialSoc:.5,initialH2:.25,solar:110,wind:40,demand:80,site:0,weather:1,hydrogen:false,grid:true};
test('72 hourly rows',()=>assert.equal(simulate(base).records.length,72));
test('battery state is bounded',()=>simulate(base).records.forEach(r=>assert(r.soc>=0&&r.soc<=80)));
test('flows are nonnegative',()=>simulate(base).records.forEach(r=>['generation','demand','charge','discharge','gridImport','gridExport'].forEach(k=>assert(r[k]>=0))));
test('battery conservation',()=>{let soc=40;for(const r of simulate(base).records){soc+=r.charge*.9-r.discharge/.9;assert(Math.abs(soc-r.soc)<1e-7)}});
test('isolated site never imports',()=>assert.equal(simulate({...base,grid:false}).summary.gridImport,0));
test('with grid, demand is served',()=>assert(Math.abs(simulate(base).summary.servedPct-100)<1e-7));
test('hydrogen contributes when disconnected',()=>{const a=simulate({...base,grid:false,solar:0,wind:0,capacity:0,hydrogen:false});const b=simulate({...base,grid:false,solar:0,wind:0,capacity:0,hydrogen:true});assert(b.summary.servedPct>a.summary.servedPct)});
