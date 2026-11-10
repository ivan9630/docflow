package fr.ivantchomte.missionflow.api;
import java.util.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;
@RestController @RequestMapping("/api/v2")
public class TicketController {
 private static final Set<String> CATS=Set.of("JAVA","DATA","IA","DEVOPS","PRODUCT");
 private static final Set<String> PRIOS=Set.of("LOW","MEDIUM","HIGH");
 private final TicketRepository repo;
 public TicketController(TicketRepository r){repo=r;}
 public record CreateRequest(@NotBlank @Size(max=140) String title,@NotBlank String category,@NotBlank String priority,@Size(max=80) String owner,@Min(0) @Max(1000) int estimateHours){}
 public record MoveRequest(@NotBlank String status){}
 @GetMapping("/health") public Map<String,String> health(){return Map.of("status","ok");}
 @GetMapping("/tickets") public List<Ticket> tickets(){return repo.findAll();}
 @PostMapping("/tickets") @ResponseStatus(HttpStatus.CREATED)
 public Ticket create(@RequestBody @Valid CreateRequest r){
  if(!CATS.contains(r.category())||!PRIOS.contains(r.priority()))throw new ResponseStatusException(HttpStatus.BAD_REQUEST,"Catégorie/priorité inconnue");
  return repo.save(new Ticket(r.title().strip(),r.category(),r.priority(),"BACKLOG",r.owner(),r.estimateHours()));
 }
 @PostMapping("/tickets/{id}/transition")
 public Ticket move(@PathVariable Long id,@RequestBody @Valid MoveRequest r){
  Ticket t=repo.findById(id).orElseThrow(()->new ResponseStatusException(HttpStatus.NOT_FOUND));
  Map<String,Set<String>> transitions=Map.of("BACKLOG",Set.of("IN_PROGRESS"),"IN_PROGRESS",Set.of("BACKLOG","REVIEW"),"REVIEW",Set.of("IN_PROGRESS","DONE"),"DONE",Set.of("REVIEW"));
  if(!transitions.getOrDefault(t.status,Set.of()).contains(r.status()))throw new ResponseStatusException(HttpStatus.CONFLICT,"Transition non autorisée");
  t.status=r.status();return repo.save(t);
 }
 @GetMapping("/metrics")
 public Map<String,Object> metrics(){
  var tickets=repo.findAll();long done=tickets.stream().filter(t->t.status.equals("DONE")).count();
  int h=tickets.stream().filter(t->!t.status.equals("DONE")).mapToInt(t->t.estimateHours).sum();
  return Map.of("total",tickets.size(),"done",done,"remainingHours",h,"completionPct",tickets.isEmpty()?0:Math.round(done*1000.0/tickets.size())/10.0);
 }
}
