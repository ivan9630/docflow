/* SAS 9.4 / SAS Studio — données entièrement fictives.
   Ajuster SAS_ROOT puis créer le dossier outputs avant exécution. */
%let SAS_ROOT=/home/u000000/sas-pilotage-performance;
%let OUT=&SAS_ROOT./outputs;
options mprint mlogic symbolgen validvarname=v7;

data work.agences;
 infile "&SAS_ROOT./data/agences.csv" dsd dlm=',' firstobs=2 truncover;
 length agency_id $3 region $36 territoire $16;
 input agency_id :$3. region :$36. territoire :$16.;
run;
data work.campagnes;
 infile "&SAS_ROOT./data/campagnes.csv" dsd dlm=',' firstobs=2 truncover;
 length campaign_id $3 canal $12;
 input campaign_id :$3. canal :$12. budget_eur :best32.;
run;
data work.interactions_source;
 infile "&SAS_ROOT./data/interactions.csv" dsd dlm=',' firstobs=2 truncover;
 length interaction_id $6 agency_id $3 campaign_id $3;
 informat jour yymmdd10.;
 input interaction_id :$6. jour :yymmdd10. agency_id :$3. campaign_id :$3.
       impressions :best32. clics :best32. contacts :best32. rdv :best32. cout_eur :best32.;
 format jour yymmdd10.;
run;

proc sort data=work.interactions_source out=work.interactions_unique dupout=work.doublons nodupkey;
 by interaction_id;
run;
proc sql;
 create table work.controles as
 select i.*, case when a.agency_id is null then 1 else 0 end as agence_inconnue,
              case when c.campaign_id is null then 1 else 0 end as campagne_inconnue
 from work.interactions_unique as i
 left join work.agences as a on i.agency_id=a.agency_id
 left join work.campagnes as c on i.campaign_id=c.campaign_id;
quit;

data work.interactions_valides work.interactions_rejetees;
 set work.controles;
 length motif_rejet $160;
 motif_rejet='';
 if agence_inconnue then motif_rejet=catx('; ',motif_rejet,'AGENCE_INCONNUE');
 if campagne_inconnue then motif_rejet=catx('; ',motif_rejet,'CAMPAGNE_INCONNUE');
 if missing(impressions) or impressions<=0 then motif_rejet=catx('; ',motif_rejet,'IMPRESSIONS_INVALIDES');
 if missing(clics) or clics<0 or clics>impressions then motif_rejet=catx('; ',motif_rejet,'CLICS_INVALIDES');
 if missing(contacts) or contacts<0 or contacts>clics then motif_rejet=catx('; ',motif_rejet,'CONTACTS_INVALIDES');
 if missing(rdv) or rdv<0 or rdv>contacts then motif_rejet=catx('; ',motif_rejet,'RDV_INVALIDES');
 if missing(cout_eur) or cout_eur<0 then motif_rejet=catx('; ',motif_rejet,'COUT_INVALIDE');
 if missing(jour) then motif_rejet=catx('; ',motif_rejet,'DATE_INVALIDE');
 if motif_rejet='' then output work.interactions_valides;
 else output work.interactions_rejetees;
run;

proc sql;
 create table work.faits_enrichis as
 select i.*, a.region, a.territoire, c.canal, c.budget_eur
 from work.interactions_valides as i
 inner join work.agences as a on i.agency_id=a.agency_id
 inner join work.campagnes as c on i.campaign_id=c.campaign_id;
quit;

%macro kpis(par=region,sortie=work.kpi_region);
 proc sql;
 create table &sortie. as
 select &par., count(*) as observations,
        sum(impressions) as impressions, sum(clics) as clics,
        sum(contacts) as contacts, sum(rdv) as rdv, sum(cout_eur) as cout_eur format=comma12.2,
        case when calculated impressions>0 then 100*calculated clics/calculated impressions else . end as ctr_pct format=8.2,
        case when calculated clics>0 then 100*calculated rdv/calculated clics else . end as conversion_rdv_pct format=8.2,
        case when calculated rdv>0 then calculated cout_eur/calculated rdv else . end as cout_par_rdv format=8.2
 from work.faits_enrichis
 group by &par.
 order by &par.;
 quit;
%mend;
%kpis(par=region,sortie=work.kpi_region);
%kpis(par=canal,sortie=work.kpi_canal);
%kpis(par=territoire,sortie=work.kpi_territoire);

proc sql;
 create table work.audit_qualite as
 select 'SOURCE' as etape length=22,count(*) as lignes from work.interactions_source
 union all select 'DOUBLONS',count(*) from work.doublons
 union all select 'REJETEES',count(*) from work.interactions_rejetees
 union all select 'VALIDES',count(*) from work.interactions_valides;
quit;

ods html path="&OUT." file="rapport_pilotage.html" style=htmlblue;
title 'Contrôles qualité';proc print data=work.audit_qualite noobs;run;
title 'Indicateurs de pilotage';proc report data=work.kpi_region nowd;
 columns region observations impressions clics rdv ctr_pct conversion_rdv_pct cout_par_rdv;
 define region / display 'Région';
 define observations / display 'Lignes';
 define impressions / display 'Impressions';
 define clics / display 'Clics';
 define rdv / display 'Rendez-vous';
 define ctr_pct / display 'CTR (%)';
 define conversion_rdv_pct / display 'RDV/Clics (%)';
 define cout_par_rdv / display 'Coût/RDV';
run;
title 'CTR par canal';proc sgplot data=work.kpi_canal;
 vbar canal / response=ctr_pct datalabel;
 yaxis label='CTR (%)';
run;title;ods html close;

proc export data=work.kpi_region outfile="&OUT./kpi_region.csv" dbms=csv replace;run;
proc export data=work.kpi_canal outfile="&OUT./kpi_canal.csv" dbms=csv replace;run;
proc export data=work.audit_qualite outfile="&OUT./audit_qualite.csv" dbms=csv replace;run;
proc export data=work.interactions_rejetees outfile="&OUT./rejets.csv" dbms=csv replace;run;