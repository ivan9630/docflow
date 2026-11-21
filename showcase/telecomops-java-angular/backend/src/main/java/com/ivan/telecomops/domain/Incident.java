package com.ivan.telecomops.domain;
import java.time.Instant;
public record Incident(long id, String title, String site, String category, String description,
                       Priority priority, Status status, Instant createdAt) {}
