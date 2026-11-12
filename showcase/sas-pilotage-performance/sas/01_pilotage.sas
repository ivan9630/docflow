/* SAS Pilotage — projet personnel, donnees synthetiques uniquement */
options nodate nonumber;
%let debut=01JAN2026;
%let fin=31MAR2026;

data dispositifs;
 length code $8 libelle $60;
 infile datalines dlm='|' truncover;
 input code :$8. libelle :$60.;
 datalines;
ACC|Accompagnement individuel
ATEL|Atelier collectif
FORM|Formation professionnelle
;
run;

data actions;
 length id 8 dispositif $8 statut $10 referent $20;
 format date_action date9.;
 infile datalines dlm='|' truncover;
 input id dispositif :$8. date_action :date9. statut :$10. referent :$20.;
 datalines;
101|ACC|05JAN2026|REALISEE|Equipe_A
102|ATEL|12JAN2026|REALISEE|Equipe_B
103|FORM|26JAN2026|PREVUE|Equipe_A
104|ACC|02FEB2026|REALISEE|Equipe_A
105|ATEL|06FEB2026|ANNULEE|Equipe_B
106|FORM|16FEB2026|REALISEE|Equipe_C
107|ACC|24FEB2026|REALISEE|Equipe_A
108|ATEL|03MAR2026|REALISEE|Equipe_B
109|FORM|11MAR2026|PREVUE|Equipe_C
110|ACC|25MAR2026|REALISEE|Equipe_A
;
run;

data participants;
 length participant_id 8 action_id 8 suivi_30j $3;
 infile datalines dlm='|' truncover;
 input participant_id action_id suivi_30j :$3.;
 datalines;
1|101|OUI
2|101|NON
3|102|OUI
4|104|OUI
5|106|NON
6|106|OUI
7|107|OUI
8|108|OUI
9|110|NON
10|110|OUI
;
run;

/* Controler les cles et la referentialite avant agregation. */
proc sql;
 create table qualite as
 select
  (select count(*) from actions where missing(id) or missing(dispositif)) as actions_cles_manquantes,
  (select count(*) from participants where missing(participant_id) or missing(action_id)) as suivis_cles_manquantes,
  (select count(*) from participants p left join actions a on p.action_id=a.id where a.id is null) as suivis_sans_action,
  (select count(*) from actions a left join dispositifs d on a.dispositif=d.code where d.code is null) as codes_dispositif_inconnus,
  (select count(*)-count(distinct id) from actions) as doublons_actions;
quit;

/* Restreindre la periode et exclure les annulations des actions planifiees. */
data actions_periode;
 set actions;
 if date_action >= "&debut"d and date_action <= "&fin"d;
 mois=intnx('month',date_action,0,'b');
 format mois monyy7.;
 if statut ne 'ANNULEE' then planifiee=1; else planifiee=0;
 if statut = 'REALISEE' then realisee=1; else realisee=0;
run;

/* Statistiques individuelles, distinctes des nombres d'actions. */
proc sql;
 create table suivis_par_action as
 select action_id,
        count(distinct participant_id) as participants,
        sum(suivi_30j='OUI') as suivis_completes
 from participants
 group by action_id;
 create table tableau_bord as
 select a.mois format=monyy7.,
        a.dispositif, d.libelle,
        count(a.id) as actions_total,
        sum(a.planifiee) as actions_planifiees,
        sum(a.realisee) as actions_realisees,
        sum(coalesce(s.participants,0)) as participants,
        sum(coalesce(s.suivis_completes,0)) as suivis_completes,
        case when calculated actions_planifiees > 0
          then calculated actions_realisees / calculated actions_planifiees
          else . end as taux_realisation format=percent8.1,
        case when calculated participants > 0
          then calculated suivis_completes / calculated participants
          else . end as taux_suivi_30j format=percent8.1
 from actions_periode a
 left join dispositifs d on a.dispositif=d.code
 left join suivis_par_action s on a.id=s.action_id
 group by a.mois,a.dispositif,d.libelle
 order by a.mois,a.dispositif;
quit;

/* Consolidation generale pour note de pilotage. */
proc sql;
 create table synthese as
 select sum(actions_planifiees) as planifiees,
        sum(actions_realisees) as realisees,
        sum(participants) as participants,
        sum(suivis_completes) as suivis_completes,
        calculated realisees/calculated planifiees as taux_realisation format=percent8.1,
        calculated suivis_completes/calculated participants as taux_suivi_30j format=percent8.1
 from tableau_bord;
quit;

title "Qualite des donnees sources";
proc print data=qualite noobs; run;
title "Indicateurs par dispositif et mois";
proc print data=tableau_bord noobs; run;
title "Synthese des actions de pilotage";
proc print data=synthese noobs; run;
title "Actions realisees par mois et dispositif";
proc sgplot data=tableau_bord;
 vbar mois / response=actions_realisees group=dispositif groupdisplay=cluster stat=sum;
 yaxis label="Nombre d'actions realisees";
 xaxis label="Mois";
run;
title;

/* Export dans le repertoire de travail SAS accessible depuis SAS Studio */
%let chemin=%sysfunc(pathname(work));
proc export data=tableau_bord outfile="&chemin./indicateurs_pilotage.csv" dbms=csv replace; run;
