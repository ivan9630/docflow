package fr.ivantchomte.missionflow;
import java.util.*;
import java.time.*;
public final class Workflow {
 private Workflow(){}
 public enum Status{BACKLOG,IN_PROGRESS,REVIEW,DONE}
 public enum Priority{LOW,MEDIUM,HIGH}
 public record Item(long id,String title,String category,Priority priority,Status status,String owner,int estimateHours,LocalDate createdAt){}
 public static String validate(String title,String category,String owner,int estimate){
  if(title==null||title.isBlank()||title.length()>140)throw new IllegalArgumentException("Titre requis (1-140 caractères)");
  if(category==null||!Set.of("DATA","JAVA","IA","DEVOPS","PRODUCT").contains(category))throw new IllegalArgumentException("Catégorie invalide");
  if(owner==null||owner.length()>80)throw new IllegalArgumentException("Responsable invalide");
  if(estimate<0||estimate>1000)throw new IllegalArgumentException("Estimation invalide");
  return title.strip();
 }
 public static void assertTransition(Status before,Status next){
  if(before==next)return;
  if(before==Status.BACKLOG&&next==Status.IN_PROGRESS)return;
  if(before==Status.IN_PROGRESS&&(next==Status.REVIEW||next==Status.BACKLOG))return;
  if(before==Status.REVIEW&&(next==Status.DONE||next==Status.IN_PROGRESS))return;
  if(before==Status.DONE&&next==Status.REVIEW)return;
  throw new IllegalArgumentException("Transition non autorisée : "+before+" -> "+next);
 }
 public static Map<String,Object> metrics(Collection<Item> items){
  int total=0,done=0,hours=0;EnumMap<Status,Integer> counts=new EnumMap<>(Status.class);
  for(Status s:Status.values())counts.put(s,0);
  for(Item i:items){total++;counts.put(i.status(),counts.get(i.status())+1);if(i.status()==Status.DONE)done++;else hours+=i.estimateHours();}
  Map<String,Object> out=new LinkedHashMap<>();out.put("total",total);out.put("done",done);
  out.put("completionPct",total==0?0:Math.round(1000.0*done/total)/10.0);
  out.put("remainingHours",hours);out.put("statuses",counts);return out;
 }
 public static List<String> acceptanceIdeas(String category){
  return switch(category){
   case "DATA" -> List.of("Contrôler les doublons et les valeurs manquantes","Documenter les sources et la qualité","Valider les indicateurs avec le métier");
   case "JAVA" -> List.of("Documenter l'API et ses erreurs","Tester les transitions et cas limites","Passer les tests automatisés");
   case "IA" -> List.of("Définir des exemples d'évaluation","Vérifier la confidentialité des données","Documenter les limites et prévoir une revue humaine");
   case "DEVOPS" -> List.of("Versionner la configuration","Vérifier le déploiement et le rollback","Documenter le traitement des incidents");
   default -> List.of("Préciser la valeur utilisateur","Définir des critères d'acceptation","Organiser la recette");
  };
 }
}
