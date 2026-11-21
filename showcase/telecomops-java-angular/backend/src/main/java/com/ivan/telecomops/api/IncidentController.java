package com.ivan.telecomops.api;
import com.ivan.telecomops.api.IncidentDtos.*;
import com.ivan.telecomops.domain.*;
import com.ivan.telecomops.service.IncidentService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import java.util.*;
@RestController
@RequestMapping("/api")
@CrossOrigin(origins="http://localhost:4200")
public class IncidentController {
    private final IncidentService service;
    public IncidentController(IncidentService service) { this.service=service; }
    @GetMapping("/incidents")
    public List<Incident> list(@RequestParam(required=false) Status status,
                               @RequestParam(required=false) Priority priority,
                               @RequestParam(required=false) String q) {
        return service.list(status,priority,q);
    }
    @GetMapping("/incidents/{id}")
    public Incident get(@PathVariable long id) { return service.get(id); }
    @PostMapping("/incidents")
    @ResponseStatus(HttpStatus.CREATED)
    public Incident create(@Valid @RequestBody NewIncident incident) { return service.create(incident); }
    @PatchMapping("/incidents/{id}/status")
    public Incident update(@PathVariable long id,@Valid @RequestBody ChangeStatus status) {
        return service.changeStatus(id,status.status());
    }
    @GetMapping("/metrics")
    public Map<String,Long> metrics() { return service.metrics(); }
}
