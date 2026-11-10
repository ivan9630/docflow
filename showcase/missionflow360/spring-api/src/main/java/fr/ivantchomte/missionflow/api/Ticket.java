package fr.ivantchomte.missionflow.api;
import jakarta.persistence.*;
import java.time.*;
@Entity @Table(name="tickets")
public class Ticket {
 @Id @GeneratedValue(strategy=GenerationType.IDENTITY) public Long id;
 @Column(nullable=false,length=140) public String title;
 @Column(nullable=false,length=20) public String category;
 @Column(nullable=false,length=10) public String priority;
 @Column(nullable=false,length=20) public String status;
 @Column(length=80) public String owner;
 public int estimateHours;
 public LocalDate createdAt;
 protected Ticket(){}
 public Ticket(String title,String category,String priority,String status,String owner,int hours){
  this.title=title;this.category=category;this.priority=priority;this.status=status;
  this.owner=owner;this.estimateHours=hours;this.createdAt=LocalDate.now();
 }
}
