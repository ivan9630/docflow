/* Matomo (Piwik) optional tracking; no network requests until explicit consent AND valid instance config. */
(function(){
 'use strict';
 const status=document.getElementById('status');
 let enabled=false;
 function send(category,action){ if(enabled && window._paq){window._paq.push(['trackEvent',category,action]);} }
 document.getElementById('cta').addEventListener('click',()=>{send('CTA','Click','solution');status.textContent='CTA enregistré localement.';});
 document.getElementById('lead').addEventListener('click',()=>{if(enabled && window._paq){window._paq.push(['trackEvent','Form','Submit','contact_demo']);window._paq.push(['trackGoal',1]);}status.textContent='Conversion de démonstration : aucun formulaire personnel envoyé.';});
 document.getElementById('consent').addEventListener('click',()=>{
   const cfg=window.MATOMO_CONFIG||{};
   if(!cfg.baseUrl||!Number.isInteger(cfg.siteId)||cfg.siteId<1||!/^https:\/\//.test(cfg.baseUrl)){status.textContent='Aucune instance Matomo configurée : tracking externe non activé.';return;}
   enabled=true;const base=cfg.baseUrl.replace(/\/+$/,'')+'/';
   window._paq=window._paq||[];
   window._paq.push(['setTrackerUrl',base+'matomo.php']);
   window._paq.push(['setSiteId',cfg.siteId]);
   window._paq.push(['setConsentGiven']);
   window._paq.push(['trackPageView']);
   window._paq.push(['enableLinkTracking']);
   if(!document.getElementById('matomo-loader')){const s=document.createElement('script');s.id='matomo-loader';s.src=base+'matomo.js';s.async=true;document.head.appendChild(s);}
   status.textContent='Tracking Matomo autorisé pour cette session.';
 });
 document.getElementById('reject').addEventListener('click',()=>{
   if(window._paq){window._paq.push(['forgetConsentGiven']);}
   enabled=false;status.textContent='Tracking révoqué. Rafraîchir la page pour décharger le script externe.';
 });
})();
