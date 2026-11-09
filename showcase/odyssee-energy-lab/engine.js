/* Odyssée Energy Lab : noyau de simulation éducatif, sans dépendances. */
(function(root) {
'use strict';
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
function shape(t,site,weather) {
 const hour=t%24,day=Math.floor(t/24);
 return {solar:clamp(Math.max(0,Math.sin(Math.PI*(hour-6)/13))*(.78+.16*Math.sin(day*1.7+site*.9))*weather,0,1),
 wind:clamp(.45+.26*Math.sin(t*.41+site*1.8)+.11*Math.cos(t*.17),.05,1),
 load:Math.max(.4,.73+.12*Math.cos((hour-19)*Math.PI/12)+.08*Math.sin(t*.19+site))};
}
function simulate(p) {
 const n=Math.max(1,Number(p.hours)||72),cap=Math.max(0,Number(p.capacity)||0),pow=Math.max(0,Number(p.power)||0),eta=clamp(Number(p.efficiency)||.9,.01,1);
 const hcap=Math.max(0,Number(p.h2Capacity)||0),hpow=Math.max(0,Number(p.h2Power)||0),heta=clamp(Number(p.h2Efficiency)||.48,.01,1);
 let soc=cap*clamp(Number(p.initialSoc)||0,0,1),h2=hcap*clamp(Number(p.initialH2)||0,0,1),load=0,gen=0,served=0,imp=0,exp=0;
 const records=[];
 for(let t=0;t<n;t++){
  const s=shape(t,Number(p.site)||0,Number(p.weather)||1);
  const production=(Number(p.solar)||0)*s.solar+(Number(p.wind)||0)*s.wind,demand=(Number(p.demand)||0)*s.load;
  load+=demand;gen+=production;
  let surplus=production-demand,charge=0,discharge=0,hcharge=0,hdischarge=0,gridImport=0,gridExport=0;
  if(surplus>=0){
   charge=Math.min(surplus,pow,(cap-soc)/eta);soc+=charge*eta;surplus-=charge;
   if(p.hydrogen){hcharge=Math.min(surplus,hpow,(hcap-h2)/heta);h2+=hcharge*heta;surplus-=hcharge;}
   gridExport=p.grid?surplus:0;exp+=gridExport;served+=demand;
  }else{
   let deficit=-surplus;discharge=Math.min(deficit,pow,soc*eta);soc-=discharge/eta;deficit-=discharge;
   if(p.hydrogen){hdischarge=Math.min(deficit,hpow,h2*heta);h2-=hdischarge/heta;deficit-=hdischarge;}
   gridImport=p.grid?deficit:0;imp+=gridImport;served+=demand-(p.grid?0:deficit);
  }
  soc=clamp(soc,0,cap);h2=clamp(h2,0,hcap);
  records.push({hour:t,generation:production,demand,soc,h2,charge,discharge,hcharge,hdischarge,gridImport,gridExport});
 }
 return {records,summary:{generation:gen,demand:load,gridImport:imp,gridExport:exp,servedPct:load?100*served/load:100,localCoveragePct:load?100*(load-imp)/load:100,finalSoc:soc,finalH2:h2}};
}
const api={simulate,shape,clamp};
if(typeof module==='object'&&module.exports)module.exports=api;else root.OdysseeEngine=api;
})(typeof window!=='undefined'?window:globalThis);