# R de base : analyse reproductible sur cohortes fictives
args <- commandArgs(trailingOnly=TRUE)
root <- if (length(args)>0) args[1] else "."
source_csv <- file.path(root,"data","campagnes_ft_pro_demo.csv")
out <- file.path(root,"output")
dir.create(out,showWarnings=FALSE,recursive=TRUE)
d <- read.csv(source_csv,stringsAsFactors=FALSE,check.names=FALSE)
d <- d[!duplicated(d$record_id), ]
ok <- d$region %in% c("Ile-de-France","Hauts-de-France","Bretagne","Occitanie","Auvergne-Rhone-Alpes") &
 d$secteur %in% c("BTP","Sante","Industrie","Commerce","Numerique") &
 d$campagne %in% c("FT-Pro-Acquisition","FT-Pro-Relance","FT-Pro-Secteurs") &
 !is.na(as.Date(d$semaine,format="%Y-%m-%d")) &
 d$impressions>0 & d$clics>=0 & d$clics<=d$impressions &
 d$contacts>=0 & d$contacts<=d$clics &
 d$rdv>=0 & d$rdv<=d$contacts & d$cout_eur>=0
clean <- d[ok,]
stopifnot(nrow(clean)==600)
clean$taux_rdv_1000 <- 1000*clean$rdv/clean$impressions
clean$ctr_pct <- 100*clean$clics/clean$impressions

# Statistiques descriptives region/secteur (taux recalcules apres agregation)
summary_group <- function(vars) {
 f <- as.formula(paste("cbind(impressions,clics,contacts,rdv,cout_eur) ~",paste(vars,collapse="+")))
 a <- aggregate(f,data=clean,FUN=sum)
 a$ctr_pct <- 100*a$clics/a$impressions
 a$rdv_pour_1000 <- 1000*a$rdv/a$impressions
 a$cout_par_rdv <- ifelse(a$rdv>0,a$cout_eur/a$rdv,NA)
 a
}
write.csv(summary_group(c("region","secteur")),file.path(out,"kpi_region_secteur_R.csv"),row.names=FALSE)
write.csv(summary_group(c("campagne","canal")),file.path(out,"kpi_campagne_canal_R.csv"),row.names=FALSE)

# Controle statistique : test t des cohortes au cours de la phase "apres"
post <- clean[clean$post==1,]
tt <- t.test(taux_rdv_1000 ~ expose, data=post)
capture.output(tt,file=file.path(out,"test_t_R.txt"))

# Difference de differences exploratoire avec variables de controle
modele <- lm(taux_rdv_1000 ~ expose*post + factor(region) + factor(secteur) + factor(campagne),data=clean)
capture.output(summary(modele),file=file.path(out,"regression_impact_R.txt"))
coef <- coef(summary(modele))
interaction <- coef["expose:post",]
result <- data.frame(indicateur="interaction_expose_post",
    coefficient=unname(interaction[1]),erreur_standard=unname(interaction[2]),
    statistique_t=unname(interaction[3]),valeur_p=unname(interaction[4]))
write.csv(result,file.path(out,"impact_R.csv"),row.names=FALSE)
cat("Analyse R terminee : 600 lignes controlees. Interpretation descriptive uniquement.\n")
