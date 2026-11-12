/* SAS 9.4 / SAS Studio — Cas d'usage fictif : campagnes employeurs.
   Parametrer ROOT en chemin absolu et creer ROOT/output avant execution. */
%let ROOT=/home/votre_utilisateur/pipeline-sas-performance;
%let SOURCE=&ROOT./data/campagnes_ft_pro_demo.csv;
%let OUT=&ROOT./output;
options validvarname=v7;
ods html path="&OUT." file="rapport_sas_campagnes.html" style=htmlblue;
ods pdf file="&OUT./rapport_sas_campagnes.pdf" style=journal;

title "Pilotage national et local des campagnes - analyse SAS";
/* 1. Ingestion */
proc import datafile="&SOURCE." out=work.brut dbms=csv replace;
 getnames=yes; guessingrows=max;
run;

/* 2. Audit qualite : unicite et coherence du parcours */
proc sort data=work.brut out=work.unique dupout=work.doublons nodupkey;
 by record_id;
run;

data work.valides work.rejets;
 set work.unique;
 length motif_rejet $80;
 motif_rejet="";
 if region not in ("Ile-de-France","Hauts-de-France","Bretagne","Occitanie","Auvergne-Rhone-Alpes")
   then motif_rejet="REGION_INCONNUE";
 else if secteur not in ("BTP","Sante","Industrie","Commerce","Numerique") then motif_rejet="SECTEUR_INCONNU";
 else if campagne not in ("FT-Pro-Acquisition","FT-Pro-Relance","FT-Pro-Secteurs") then motif_rejet="CAMPAGNE_INCONNUE";
 else if missing(input(semaine,yymmdd10.)) then motif_rejet="DATE_INVALIDE";
 else if missing(impressions) or impressions<=0 or clics<0 or clics>impressions
   then motif_rejet="CLICS_IMPRESSIONS_INCOHERENTS";
 else if missing(contacts) or contacts<0 or contacts>clics or missing(rdv) or rdv<0 or rdv>contacts
   then motif_rejet="PARCOURS_INCOHERENT";
 else if missing(cout_eur) or cout_eur<0 then motif_rejet="COUT_NEGATIF";
 else if expose not in (0,1) or post not in (0,1) then motif_rejet="GROUPE_INCOHERENT";
 if motif_rejet="" then do;
  taux_rdv_1000=1000*rdv/impressions;
  ctr_pct=100*clics/impressions;
  if clics>0 then taux_contact_pct=100*contacts/clics;
  else taux_contact_pct=.;
  if rdv>0 then cout_par_rdv=cout_eur/rdv;
  else cout_par_rdv=.;
  output work.valides;
 end;
 else output work.rejets;
run;

proc sql;
 create table work.audit as
 select "Brut" as etape length=26,count(*) as lignes from work.brut
 union all select "Doublons",count(*) from work.doublons
 union all select "Rejets metier",count(*) from work.rejets
 union all select "Valides",count(*) from work.valides;
quit;

title2 "Audit qualite et tracabilite";
proc print data=work.audit noobs;run;

/* 3. Pilotage multi-axes ; ratios des sommes (pas moyenne des CTR) */
%macro synthese(dim);
proc sql;
 create table work.kpi_&dim. as
 select &dim.,count(*) as observations,
        sum(impressions) as impressions,
        sum(clics) as clics,
        sum(contacts) as contacts,
        sum(rdv) as rdv,
        sum(cout_eur) as cout_eur format=12.2,
        case when calculated impressions>0 then 100*calculated clics/calculated impressions else . end as ctr_pct format=8.2,
        case when calculated clics>0 then 100*calculated contacts/calculated clics else . end as contact_pct format=8.2,
        case when calculated rdv>0 then calculated cout_eur/calculated rdv else . end as cout_par_rdv format=10.2
 from work.valides
 group by &dim.
 order by &dim.;
quit;
proc export data=work.kpi_&dim. outfile="&OUT./kpi_&dim._sas.csv" dbms=csv replace;run;
%mend;
%synthese(region);
%synthese(secteur);
%synthese(campagne);
%synthese(canal);

title2 "Performance territoriale";
proc report data=work.kpi_region nowd;
 columns region observations impressions clics rdv ctr_pct contact_pct cout_par_rdv;
 define region / display "Region";
 define observations / display "Observations";
 define impressions / display "Impressions";
 define clics / display "Clics";
 define rdv / display "RDV";
 define ctr_pct / display "CTR (%)";
 define contact_pct / display "Contact / clic (%)";
 define cout_par_rdv / display "Cout / RDV";
run;
title2 "Suivi sectoriel";
proc report data=work.kpi_secteur nowd;run;
title2 "Campagnes";
proc report data=work.kpi_campagne nowd;run;
title2 "Evolution territoriale du taux de RDV";
proc sgplot data=work.valides;
 vbar region / response=rdv stat=sum datalabel;
 yaxis label="Nombre de rendez-vous";
run;

/* 4. Evaluation exploratoire des actions, non causale */
title2 "TTEST post-campagne : expose vs temoin";
proc ttest data=work.valides(where=(post=1)) sides=2 alpha=0.05;
 class expose;
 var taux_rdv_1000;
run;
title2 "ANOVA/GLM : interaction expose x post, controles region/secteur/campagne";
proc glm data=work.valides;
 class region secteur campagne;
 model taux_rdv_1000 = expose post expose*post region secteur campagne / solution;
run;quit;

/* 5. Restitution pour equipes metier et audit */
proc export data=work.audit outfile="&OUT./audit_qualite_sas.csv" dbms=csv replace;run;
proc export data=work.rejets outfile="&OUT./rejets_sas.csv" dbms=csv replace;run;
ods pdf close;
ods html close;
title;
