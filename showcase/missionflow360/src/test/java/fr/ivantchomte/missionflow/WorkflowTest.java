package fr.ivantchomte.missionflow;
import java.time.*;
import java.util.*;
public class WorkflowTest {
 static void check(boolean ok){if(!ok)throw new AssertionError("Échec de test");}
 public static void main(String[] args){
  check(Workflow.validate(" Bonjour ","JAVA","Ivan",3).equals("Bonjour"));
  try{Workflow.validate("","JAVA","Ivan",3);throw new AssertionError();}catch(IllegalArgumentException expected){}
  try{Workflow.validate("Ticket","DATA","Ivan",-1);throw new AssertionError();}catch(IllegalArgumentException expected){}
  Workflow.assertTransition(Workflow.Status.BACKLOG,Workflow.Status.IN_PROGRESS);
  Workflow.assertTransition(Workflow.Status.REVIEW,Workflow.Status.DONE);
  try{Workflow.assertTransition(Workflow.Status.BACKLOG,Workflow.Status.DONE);throw new AssertionError();}catch(IllegalArgumentException expected){}
  var a=new Workflow.Item(1,"Ticket","JAVA",Workflow.Priority.HIGH,Workflow.Status.BACKLOG,"Ivan",12,LocalDate.now());
  var b=new Workflow.Item(2,"Terminé","DATA",Workflow.Priority.MEDIUM,Workflow.Status.DONE,"Data",5,LocalDate.now());
  var stats=Workflow.metrics(List.of(a,b));check(stats.get("total").equals(2));check(stats.get("remainingHours").equals(12));
  check(Workflow.acceptanceIdeas("JAVA").size()==3);
  System.out.println("8 domain checks passed");
 }
}
