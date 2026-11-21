import { Component,OnInit,inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs';
import { IncidentService } from './incident.service';
import { CreateIncident,Incident,Metrics,Priority,Status } from './incident.model';
@Component({
 selector:'app-root',standalone:true,imports:[CommonModule,FormsModule],
 templateUrl:'./app.component.html',styleUrl:'./app.component.css'
})
export class AppComponent implements OnInit {
 private api=inject(IncidentService);
 incidents:Incident[]=[];
 metrics:Metrics={total:0,open:0,inProgress:0,resolved:0,critical:0};
 priorities:Priority[]=['LOW','MEDIUM','HIGH','CRITICAL'];
 statuses:Status[]=['OPEN','IN_PROGRESS','RESOLVED'];
 query=''; statusFilter:Status|'ALL'='ALL';priorityFilter:Priority|'ALL'='ALL';
 loading=false;saving=false;error='';success='';
 form:CreateIncident={title:'',site:'',category:'FIBER',description:'',priority:'MEDIUM'};
 ngOnInit(){this.refresh();}
 refresh(){
   this.loading=true;this.error='';
   this.api.list({status:this.statusFilter,priority:this.priorityFilter,q:this.query})
    .pipe(finalize(()=>this.loading=false))
    .subscribe({next:records=>this.incidents=records,error:()=>this.error='Impossible de joindre l’API Java (port 8080).'});
   this.api.metrics().subscribe({next:m=>this.metrics=m,error:()=>{}});
 }
 create(){
   if(!this.form.title.trim()||!this.form.site.trim()||!this.form.category.trim())return;
   this.saving=true;this.error='';this.success='';
   this.api.create(this.form).pipe(finalize(()=>this.saving=false)).subscribe({
     next:()=>{this.form={title:'',site:'',category:'FIBER',description:'',priority:'MEDIUM'};this.success='Incident créé.';this.refresh();},
     error:()=>this.error='Création impossible. Vérifie le formulaire et l’API.'
   });
 }
 setStatus(i:Incident,status:Status){
   this.api.setStatus(i.id,status).subscribe({
     next:()=>{this.success='Statut modifié.';this.refresh();},
     error:()=>this.error='Mise à jour impossible.'
   });
 }
 priorityName(p:Priority){return ({LOW:'Faible',MEDIUM:'Moyenne',HIGH:'Haute',CRITICAL:'Critique'})[p];}
 statusName(s:Status){return ({OPEN:'Ouvert',IN_PROGRESS:'En traitement',RESOLVED:'Résolu'})[s];}
}
