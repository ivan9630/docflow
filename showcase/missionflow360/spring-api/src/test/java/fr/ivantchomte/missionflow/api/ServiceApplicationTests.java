package fr.ivantchomte.missionflow.api;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import static org.junit.jupiter.api.Assertions.*;
@SpringBootTest
class ServiceApplicationTests {
 @Test void contextLoads(){}
 @Test void ticketDefaults(){Ticket t=new Ticket("Demo","JAVA","LOW","BACKLOG","Dev",3);assertEquals("BACKLOG",t.status);assertNotNull(t.createdAt);}
}
