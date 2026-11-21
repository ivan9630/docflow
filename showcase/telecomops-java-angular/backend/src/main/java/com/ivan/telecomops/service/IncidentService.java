package com.ivan.telecomops.service;
import com.ivan.telecomops.api.IncidentDtos.NewIncident;
import com.ivan.telecomops.domain.*;
import org.springframework.stereotype.Service;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;

@Service
public class IncidentService {
    private final Map<Long,Incident> records=new ConcurrentHashMap<>();
    private final AtomicLong sequence=new AtomicLong();
    public IncidentService() {
        seed("Dégradation fibre optique","PAR-NORD-12","FIBER","Latence intermittente",Priority.HIGH,Status.OPEN);
        seed("Alerte antenne 5G","LYO-EST-03","RADIO","Mesures de signal hors seuil",Priority.CRITICAL,Status.IN_PROGRESS);
        seed("Maintenance routeur coeur","MAR-SUD-08","CORE","Redémarrage planifié",Priority.MEDIUM,Status.RESOLVED);
        seed("Pertes de paquets accès entreprise","LIL-CENTRE-21","IP","Dégradation QoS",Priority.HIGH,Status.OPEN);
        seed("Incident DSLAM","NAN-OUEST-07","ACCESS","Synchronisation instable",Priority.LOW,Status.OPEN);
    }
    private void seed(String title,String site,String category,String description,Priority priority,Status status) {
        long id=sequence.incrementAndGet();
        records.put(id,new Incident(id,title,site,category,description,priority,status,Instant.now()));
    }
    public List<Incident> list(Status status,Priority priority,String q) {
        String query=q==null?"":q.strip().toLowerCase(Locale.ROOT);
        return records.values().stream()
            .filter(i->status==null||i.status()==status)
            .filter(i->priority==null||i.priority()==priority)
            .filter(i->query.isBlank()||i.title().toLowerCase(Locale.ROOT).contains(query)
                ||i.site().toLowerCase(Locale.ROOT).contains(query)
                ||i.category().toLowerCase(Locale.ROOT).contains(query))
            .sorted(Comparator.comparing(Incident::createdAt).reversed().thenComparing(Incident::id))
            .collect(Collectors.toList());
    }
    public Incident get(long id) {
        Incident i=records.get(id);
        if(i==null) throw new NoSuchElementException("Incident introuvable : "+id);
        return i;
    }
    public Incident create(NewIncident data) {
        long id=sequence.incrementAndGet();
        Incident incident=new Incident(id,data.title().strip(),data.site().strip(),data.category().strip(),
            data.description()==null?"":data.description().strip(),data.priority(),Status.OPEN,Instant.now());
        records.put(id,incident); return incident;
    }
    public Incident changeStatus(long id,Status status) {
        return records.compute(id,(key,previous)->{
            if(previous==null) throw new NoSuchElementException("Incident introuvable : "+id);
            return new Incident(previous.id(),previous.title(),previous.site(),previous.category(),
                previous.description(),previous.priority(),status,previous.createdAt());
        });
    }
    public Map<String,Long> metrics() {
        List<Incident> all=new ArrayList<>(records.values());
        return Map.of("total",(long)all.size(),"open",all.stream().filter(i->i.status()==Status.OPEN).count(),
            "inProgress",all.stream().filter(i->i.status()==Status.IN_PROGRESS).count(),
            "resolved",all.stream().filter(i->i.status()==Status.RESOLVED).count(),
            "critical",all.stream().filter(i->i.priority()==Priority.CRITICAL).count());
    }
}
