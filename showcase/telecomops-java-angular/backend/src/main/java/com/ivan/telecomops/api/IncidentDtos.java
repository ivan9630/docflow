package com.ivan.telecomops.api;
import com.ivan.telecomops.domain.Priority;
import com.ivan.telecomops.domain.Status;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
public final class IncidentDtos {
    private IncidentDtos(){}
    public record NewIncident(
        @NotBlank @Size(max=120) String title,
        @NotBlank @Size(max=80) String site,
        @NotBlank @Size(max=40) String category,
        @Size(max=2000) String description,
        @NotNull Priority priority
    ) {}
    public record ChangeStatus(@NotNull Status status) {}
}
