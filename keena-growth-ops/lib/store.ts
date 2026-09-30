import { mkdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { DatabaseSync } from 'node:sqlite';
import { scoreCandidate, isoWeekKey, type Lead } from './scoring';
export interface IngestRun {runAt:string;isoWeek:string;candidatesReviewed:number;added:number;skippedDuplicate:number;skippedOutOfIcp:number;skippedExpired:number;skippedOverTarget:number;}
export interface PipelineData {leads:Lead[];runs:IngestRun[];}
function defaultDataFile(){return process.env.KEENA_DEMO==='1'?path.join(process.cwd(),'.demo','pipeline.json'):process.env.KEENA_DATA_FILE??path.join(process.cwd(),'.local','pipeline.json');}
function initial(file:string):PipelineData {
  try {const data=JSON.parse(readFileSync(file,'utf8'));if(!Array.isArray(data.leads)||!Array.isArray(data.runs))throw Error('Invalid legacy pipeline');return data;}catch(error){if((error as NodeJS.ErrnoException).code!=='ENOENT')throw error;}
  if(process.env.KEENA_DEMO==='1' && file===defaultDataFile()) {
    const now=new Date();const leads=['Fictional Harbor Clinic','Fictional Valley Care','Fictional Sample Health'].map((organization,i)=>scoreCandidate({organization,title:'Example EHR conversion opportunity',text:'electronic health record conversion services',sourceType:i===1?'job_posting':'rfp',url:`https://example.invalid/keena/${i}`,checkedAt:now.toISOString(),deadline:new Date(now.getTime()+86400000*14).toISOString()},isoWeekKey(now),now)!);
    return {leads,runs:[]};
  }
  return {leads:[],runs:[]};
}
export function mutatePipeline<T>(fn:(data:PipelineData)=>T,file=defaultDataFile()):T {
  mkdirSync(path.dirname(file),{recursive:true});const db=new DatabaseSync(file+'.sqlite');
  try {db.exec('PRAGMA busy_timeout=5000;CREATE TABLE IF NOT EXISTS pipeline(id INTEGER PRIMARY KEY CHECK(id=1),value TEXT NOT NULL);BEGIN IMMEDIATE;');
    const row=db.prepare('SELECT value FROM pipeline WHERE id=1').get() as {value:string}|undefined;
    const data:PipelineData=row?JSON.parse(row.value):initial(file);
    const result=fn(data);db.prepare('INSERT INTO pipeline VALUES(1,?) ON CONFLICT(id) DO UPDATE SET value=excluded.value').run(JSON.stringify(data));db.exec('COMMIT');return result;
  }catch(error){if(db.isTransaction)db.exec('ROLLBACK');throw error;}finally{db.close();}
}
export async function loadPipeline(file?:string):Promise<PipelineData>{return mutatePipeline(data=>structuredClone(data),file);}
export function leadsAddedThisWeek(data:PipelineData,week:string){return data.leads.filter(l=>l.weekAdded===week).length;}
export async function updateLead(id:string,patch:Partial<Pick<Lead,'stage'|'notes'|'owner'>>,file?:string,expectedVersion?:number):Promise<Lead|null>{return mutatePipeline(data=>{const lead=data.leads.find(l=>l.id===id);if(!lead)return null;if(expectedVersion!==undefined && expectedVersion!==(lead.version??0))throw Error('stale_version');Object.assign(lead,patch,{version:(lead.version??0)+1});return structuredClone(lead);},file);}
