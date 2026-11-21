import { Injectable,inject } from '@angular/core';
import { HttpClient,HttpParams } from '@angular/common/http';
import { CreateIncident,Incident,Metrics,Priority,Status } from './incident.model';
@Injectable({providedIn:'root'})
export class IncidentService {
 private http=inject(HttpClient);
 private api='http://localhost:8080/api';
 list(filters:{status?:Status|'ALL',priority?:Priority|'ALL',q?:string}={}) {
   let params=new HttpParams();
   if(filters.status&&filters.status!=='ALL')params=params.set('status',filters.status);
   if(filters.priority&&filters.priority!=='ALL')params=params.set('priority',filters.priority);
   if(filters.q?.trim())params=params.set('q',filters.q.trim());
   return this.http.get<Incident[]>(this.api+'/incidents',{params});
 }
 metrics(){return this.http.get<Metrics>(this.api+'/metrics');}
 create(payload:CreateIncident){return this.http.post<Incident>(this.api+'/incidents',payload);}
 setStatus(id:number,status:Status){return this.http.patch<Incident>(this.api+'/incidents/'+id+'/status',{status});}
}
