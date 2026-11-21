export type Priority='LOW'|'MEDIUM'|'HIGH'|'CRITICAL';
export type Status='OPEN'|'IN_PROGRESS'|'RESOLVED';
export interface Incident { id:number; title:string; site:string; category:string; description:string; priority:Priority; status:Status; createdAt:string; }
export type CreateIncident=Pick<Incident,'title'|'site'|'category'|'description'|'priority'>;
export interface Metrics {total:number;open:number;inProgress:number;resolved:number;critical:number;}
