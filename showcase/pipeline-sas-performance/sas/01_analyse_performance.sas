/* Pipeline pédagogique SAS 9.4 / SAS Studio. Données 100 % fictives.
   Définir BASE vers le dossier racine, puis créer output/. */
%let BASE=.;

ods html path="&BASE./output" file="rapport_sas_execute.html" style=htmlblue;
title "Pipeline d'analyse de performance - pilotage stratégique";

/* Ingestion et contrôles */
proc import datafile="&BASE./data/performance_demo.csv"
  out=work.performance dbms=csv replace;
  guessingrows=max;
run;

data work.performance_clean;
 set work.performance;
 ecart_recalcule=valeur-cible;
 if missing(KPI) or missing(periode) or missing(valeur) or missing(cible) then delete;
 format ecart_recalcule 8.2;
run;

/* Analyse descriptive : valeur observée, cible, écart */
title2 "Statistiques descriptives par indicateur";
proc means data=work.performance_clean n mean std min max;
 class KPI;
 var valeur cible ecart_recalcule;
run;

/* Test bilatéral H0 : écart moyen à la cible = 0 */
proc sort data=work.performance_clean;
 by KPI;
run;
title2 "Tests t par indicateur";
proc ttest data=work.performance_clean h0=0 sides=2 alpha=.05;
 by KPI;
 var ecart_recalcule;
run;

/* ANOVA exploratoire ; unités hétérogènes, non appropriée à une comparaison métier brute */
title2 "ANOVA pédagogique";
proc glm data=work.performance_clean;
 class KPI;
 model ecart_recalcule=KPI;
run;
quit;

/* Synthèse opérationnelle */
title2 "Table de suivi";
proc report data=work.performance_clean nowd;
 columns KPI periode valeur cible ecart_recalcule;
 define KPI / display;
 define periode / display;
 define valeur / display;
 define cible / display;
 define ecart_recalcule / display "Écart à la cible";
run;

ods html close;
title;
