package fr.ivantchomte.missionflow.api;
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.annotation.*;
@SpringBootApplication
public class ServiceApplication {
 public static void main(String[] a){SpringApplication.run(ServiceApplication.class,a);}
 @Bean CommandLineRunner seed(TicketRepository repo){return a->{
  if(repo.count()==0){
   repo.save(new Ticket("Concevoir un modèle de données","DATA","HIGH","IN_PROGRESS","Data",12));
   repo.save(new Ticket("Tester un assistant documentaire","IA","MEDIUM","REVIEW","Produit",15));
  }
 };}
}
