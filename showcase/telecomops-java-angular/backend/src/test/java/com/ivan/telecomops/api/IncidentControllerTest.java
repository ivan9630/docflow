package com.ivan.telecomops.api;
import com.ivan.telecomops.TelecomOpsApplication;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
@SpringBootTest(classes=TelecomOpsApplication.class)
@AutoConfigureMockMvc
class IncidentControllerTest {
    @Autowired MockMvc mvc;
    @Test void listAndMetrics() throws Exception {
        mvc.perform(get("/api/incidents")).andExpect(status().isOk()).andExpect(jsonPath("$[0].id").exists());
        mvc.perform(get("/api/metrics")).andExpect(status().isOk()).andExpect(jsonPath("$.total").exists());
    }
    @Test void createValidateAndTransition() throws Exception {
        mvc.perform(post("/api/incidents").contentType(MediaType.APPLICATION_JSON)
            .content("{\"title\":\"Perte fibre\",\"site\":\"PAR-01\",\"category\":\"FIBER\",\"priority\":\"HIGH\"}"))
            .andExpect(status().isCreated()).andExpect(jsonPath("$.status").value("OPEN"));
        mvc.perform(post("/api/incidents").contentType(MediaType.APPLICATION_JSON).content("{}"))
            .andExpect(status().isBadRequest());
        mvc.perform(patch("/api/incidents/1/status").contentType(MediaType.APPLICATION_JSON)
            .content("{\"status\":\"RESOLVED\"}")).andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("RESOLVED"));
    }
    @Test void notFound() throws Exception {
        mvc.perform(get("/api/incidents/9999")).andExpect(status().isNotFound());
    }
}
