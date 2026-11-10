package fr.ivantchomte.missionflow.api;
import org.springframework.data.jpa.repository.JpaRepository;
public interface TicketRepository extends JpaRepository<Ticket,Long> {}
