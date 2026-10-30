import { useEffect, useState, type FormEvent } from "react";
import type { Assessment, Entry, EvidenceFile, Project, Ref } from "./types";

const reviewers = [
 ["evidence","01","Evidence examiner","Do the conclusions follow the evidence?"],
 ["engineer","02","Engineer","Does the implementation support the claim?"],
 ["sceptic","03","Sceptic","What fails, leaks, or can be misused?"],
 ["impact","04","Impact reviewer","Who benefits, and how do we know?"],
 ["delivery","05","Delivery reviewer","Can someone reproduce the work?"],
];
const blank:Project = {title:"",research_question:"",findings:"",methods:"",results:"",limitations:"",files:[]};
const sample:Project = {title:"Pump Watch: early maintenance alerts",
 research_question:"Can low-cost alerts reduce handpump downtime in a rural ward?",
 findings:"Five interviewed users reported faster maintenance after SMS alerts were introduced.",
 methods:"Interviewed five users after a two-week pilot. No control group was used.",
 results:"Three users reported fewer outages. No baseline downtime measurements were collected.",
 limitations:"Small convenience sample; self-reported outcomes; no measured comparison.",
 files:[{name:"pilot-notes.md",content:"# Pilot notes\nParticipants: 5\nDuration: 2 weeks\nBaseline measurements: not collected\nFollow-up: needed"}]};
const fieldInfo = [
 ["research_question","Research question","What did the project set out to establish?",10000],
 ["findings","Student findings","State the conclusions you want the council to examine.",20000],
 ["methods","Methods","How was the work carried out? Include sampling and comparisons.",20000],
 ["results","Results","Provide observations, measurements and baselines.",20000],
 ["limitations","Known limitations","Describe missing evidence, constraints and unfinished work.",10000],
] as const;
const accept = ".txt,.md,.csv,.py,.js,.jsx,.ts,.tsx,.dart,.java,.go,.rs,.html,.css,.sql,.json,.yaml,.yml,.c,.cpp,.h";
function refs(values:Ref[]) {return values.map(r=>r.evidence_id+":L"+r.start_line+"–"+r.end_line).join(", ");}
async function request<T>(path:string,init?:RequestInit):Promise<T> {
 const response = await fetch(path,init);
 const body = await response.json();
 if(!response.ok) {
  const message = Array.isArray(body.detail) ? body.detail.map((e:{loc:unknown[];msg:string})=>e.loc.join(".")+": "+e.msg).join("; ") : body.detail;
  throw new Error(message || "Request failed ("+response.status+").");
 }
 return body as T;
}
export function App() {
 const [project,setProject] = useState<Project>(blank);
 const [history,setHistory] = useState<Entry[]>([]);
 const [selected,setSelected] = useState<Assessment|null>(null);
 const [busy,setBusy] = useState(false);
 const [error,setError] = useState("");
 const [mode,setMode] = useState("unknown");
 const [tab,setTab] = useState<"submit"|"report">("submit");
 const [key,setKey] = useState<{body:string;value:string}|null>(null);
 const [loadingId,setLoadingId] = useState("");
 async function refresh() {setHistory(await request<Entry[]>("/v1/assessments"));}
 useEffect(()=>{
  let active=true;
  Promise.all([request<{mode:string}>("/health"),request<Entry[]>("/v1/assessments")])
   .then(([health,entries])=>{if(active){setMode(health.mode);setHistory(entries);}})
   .catch(e=>{if(active)setError(String(e.message));});
  return ()=>{active=false;};
 },[]);
 useEffect(()=>{
  if(!selected || !["queued","running"].includes(selected.status))return;
  let active=true;
  const timer = window.setInterval(()=>{
   request<Assessment>("/v1/assessments/"+selected.id).then(value=>{
    if(active){setSelected(value); if(["completed","incomplete"].includes(value.status))void refresh().catch(e=>setError(e.message));}
   }).catch(e=>{if(active)setError(e.message);});
  },1200);
  return ()=>{active=false;window.clearInterval(timer);};
 },[selected?.id,selected?.status]);
 async function open(id:string) {
  setError("");setLoadingId(id);
  try {setSelected(await request<Assessment>("/v1/assessments/"+id));setTab("report");}
  catch(e){setError((e as Error).message);}
  finally {setLoadingId("");}
 }
 async function submit(e:FormEvent) {
  e.preventDefault();setBusy(true);setError("");
  const body=JSON.stringify(project);
  const value=key?.body===body?key.value:crypto.randomUUID();
  setKey({body,value});
  try{
   const created=await request<{id:string}>("/v1/assessments",{method:"POST",headers:{"Content-Type":"application/json","Idempotency-Key":value},body});
   await open(created.id);await refresh();
  }catch(e){setError((e as Error).message);}
  finally{setBusy(false);}
 }
 async function filesChanged(files:FileList|null) {
  if(!files)return;
  setError("");
  try {
   if(files.length+project.files.length>20)throw new Error("At most 20 files are accepted.");
   const added:EvidenceFile[]=[];
   for(const file of Array.from(files)){
    if(!accept.split(",").includes("."+file.name.split(".").pop()?.toLowerCase()))throw new Error("Unsupported file: "+file.name);
    if(file.size>200000)throw new Error("File is too large: "+file.name);
    const content=new TextDecoder("utf-8",{fatal:true}).decode(await file.arrayBuffer());
    if(content.length>50000 || !content.trim() || /[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(content))throw new Error("Invalid or oversized text file: "+file.name);
    added.push({name:file.name,content});
   }
   const next=[...project.files,...added];
   if(new Set(next.map(f=>f.name.toLowerCase())).size!==next.length)throw new Error("Duplicate filenames are not accepted.");
   setProject(p=>({...p,files:next}));
  }catch(e){setError((e as Error).message);}
 }
 async function retry() {
  if(!selected)return;
  setBusy(true);setError("");
  try{await request("/v1/assessments/"+selected.id+"/retry",{method:"POST",headers:{"Idempotency-Key":crypto.randomUUID()}});await open(selected.id);await refresh();}
  catch(e){setError((e as Error).message);}finally{setBusy(false);}
 }
 const report=selected?.report;
 return <div className="app">
  <a className="skip" href="#workspace">Skip to workspace</a>
  <aside className="sidebar">
   <a className="brand" href="/" aria-label="AI Council home"><span className="brand-mark">C<span>5</span></span><span>AI Council<small>PROJECT REVIEW LAB</small></span></a>
   <div className="sidebar-label">WORKSPACE</div>
   <button className={tab==="submit"?"nav active":"nav"} onClick={()=>setTab("submit")}><span>01</span> New assessment <b>↗</b></button>
   <button className={tab==="report"?"nav active":"nav"} onClick={()=>setTab("report")}><span>02</span> Report viewer <b>↗</b></button>
   <div className="history-head"><span className="sidebar-label">RECENT ASSESSMENTS</span><button onClick={()=>void refresh().catch(e=>setError(e.message))} aria-label="Refresh history">↻</button></div>
   <div className="history">
    {!history.length && <p className="muted">Your assessment history will appear here.</p>}
    {history.map(item=><button key={item.id} onClick={()=>void open(item.id)} className={selected?.id===item.id?"history-item selected":"history-item"} disabled={loadingId===item.id}>
     <span>{item.title}</span><small><i className={"dot "+item.status}/>{item.status} · {new Date(item.created_at).toLocaleDateString()}</small></button>)}
   </div>
   <div className="sidebar-foot"><strong>Evidence over confidence.</strong><p>Five perspectives. One honest account of what your work establishes.</p><span>INDEPENDENT COUNCIL / v1.0</span></div>
  </aside>
  <div className="main">
   <header><span>Research workspace <span className="slash">/</span> {tab==="submit"?"New assessment":"Council report"}</span><span className="pill">{mode==="simulation"?"LOCAL · SIMULATION":mode==="unknown"?"CONNECTING":"LIVE · ADVISORY"}</span></header>
   <main id="workspace">
    <div className="notice" role="status"><span className="notice-dot"/><div><strong>{mode==="simulation"?"Simulation workspace":mode==="unknown"?"Checking workspace mode":"Advisory evaluation"}</strong><span>{mode==="simulation"?"Real workflow and PDFs. Simulated reviews, not judgments of your project.":mode==="unknown"?"Please wait for the server connection.":"Review the evidence and limitations. Faculty retain academic judgment."}</span></div></div>
    {error && <div className="error" role="alert">{error}<button onClick={()=>setError("")} aria-label="Dismiss error">×</button></div>}
    <section className="intro"><div><div className="eyebrow">THE FIVE-PERSPECTIVE REVIEW</div><h1>{tab==="submit"?<>Good findings deserve<br/><em>tough questions.</em></>:"The council’s report."}</h1><p>{tab==="submit"?"Bring your findings, methods and evidence. The council examines what holds up, what is missing, and what to improve next.":"A detailed critique of the submitted evidence. Read the limitations alongside every conclusion."}</p></div><div className="intro-index"><b>05</b><span>distinct perspectives<br/>zero automatic grades</span></div></section>
    <div className="reviewer-strip" aria-label="Council reviewers">{reviewers.map(([id,num,name,desc])=><div key={id}><span>{num}</span><h2>{name}</h2><p>{desc}</p></div>)}</div>
    {tab==="submit"?<form onSubmit={submit} className="work-grid">
     <section className="paper"><div className="section-heading"><div><span className="eyebrow">01 / PROJECT DOSSIER</span><h2>Tell us what you found.</h2></div><button type="button" className="text-button" onClick={()=>{setProject(sample);setKey(null);}}>Load example</button></div>
      <label>Project title<input required maxLength={200} value={project.title} onChange={e=>setProject({...project,title:e.target.value})} placeholder="A clear name for your project"/></label>
      {fieldInfo.map(([key,label,hint,max])=><label key={key}>{label}<span className="field-hint">{hint}</span><textarea required={key==="research_question"||key==="findings"} rows={key==="findings"?5:3} maxLength={max} value={project[key]} onChange={e=>setProject({...project,[key]:e.target.value})}/></label>)}
     </section>
     <aside className="dossier-aside"><section className="paper upload"><span className="eyebrow">02 / SUPPORTING EVIDENCE</span><h2>Show the work.</h2><p>Attach text, notes, data or source files. Files are read as evidence and never executed.</p>
      <label className="file-label">Supporting text and source files<input aria-label="Supporting text and source files" type="file" multiple accept={accept} onChange={e=>{void filesChanged(e.target.files);e.target.value="";}}/><span className="file-cta" aria-hidden="true">+ Choose evidence files</span></label>
      <small>20 files · 50,000 characters each<br/>200,000 characters total, including project fields</small>
      <ul className="file-list">{project.files.map(f=><li key={f.name}><span>{f.name}<small>{f.content.length.toLocaleString()} characters</small></span><button type="button" aria-label={"Remove "+f.name} onClick={()=>setProject({...project,files:project.files.filter(x=>x.name!==f.name)})}>×</button></li>)}</ul>
     </section><section className="submit-card"><span className="eyebrow">03 / COUNCIL REPORT</span><h2>Critique you can act on.</h2><ul><li>Evidence-linked strengths</li><li>Severity-ranked shortcomings</li><li>Specific improvements and checks</li><li>A detailed downloadable PDF</li></ul><p>Only supplied evidence is assessed. Missing evidence is not a failed claim.</p><button className="primary" disabled={busy||mode==="unknown"}>{busy?"Preparing assessment…":"Generate council report"}<span>↗</span></button><small>{mode==="simulation"?"Simulation PDFs are watermarked. Faculty delivery is not connected in this local workspace.":"Integrated reports are shared with the assigned faculty through JanMaang."}</small></section></aside>
    </form>:!selected?<section className="paper empty"><h2>No report selected.</h2><p>Open an assessment from your history, or start a new one.</p><button className="primary" onClick={()=>setTab("submit")}>New assessment ↗</button></section>:<section className="paper report">
     <div className="section-heading"><div><span className="eyebrow">ASSESSMENT / {selected.status.toUpperCase()}</span><h2>{selected.project.title}</h2><p>{new Date(selected.created_at).toLocaleString()} · {selected.completed_reviewers}/5 reviewers complete</p></div>{selected.status==="completed"&&report&&<a className="primary" href={"/v1/assessments/"+selected.id+"/pdf"}>Download PDF ↓</a>}</div>
     <div role="status">{["queued","running"].includes(selected.status)&&<p className="progress">Review in progress. This page updates automatically.</p>}{selected.error&&<div className="error">{selected.error}</div>}</div>
     {selected.status==="incomplete"&&<button className="primary" disabled={busy} onClick={()=>void retry()}>Retry incomplete assessment</button>}
     {report&&selected.status==="completed"&&<><p className="report-summary">{report.summary}</p><div className="meta">MODEL / {report.model} · PROMPTS / {report.prompt_version}</div>
      <h3>Prioritized improvements</h3>{report.priorities.length===0&&<p>No shortcomings reported. This is not proof of correctness.</p>}{report.priorities.map((group,i)=><article className="priority" key={i}><span className={"severity "+group.severity.toLowerCase()}>{group.severity}</span><h4>{group.title}</h4>{group.disagreement&&<strong>Reviewer disagreement — inspect both judgments.</strong>}{group.issues.map((issue,j)=><p key={j}>{issue.improvement}<br/><small>Verify: {issue.verification}</small></p>)}</article>)}
      <h3>Five perspectives</h3>{report.reviewers.map(review=><details key={review.reviewer} open><summary>{reviewers.find(r=>r[0]===review.reviewer)?.[2]}</summary><h4>What is good</h4>{!review.strengths.length&&<p>No supported strengths identified.</p>}{review.strengths.map((s,i)=><p key={i}>{s.detail}<small className="reference">{refs(s.evidence)}</small></p>)}<h4>Shortcomings and improvements</h4>{review.issues.map((issue,i)=><article className="finding" key={i}><span className={"severity "+issue.severity.toLowerCase()}>{issue.severity}</span><h4>{issue.title}</h4><small className="claim">{issue.claim_status.replaceAll("_"," ")}</small><p>{issue.detail}</p><p><b>Consequence:</b> {issue.consequence}</p><p><b>Improve:</b> {issue.improvement}</p><p><b>Verify:</b> {issue.verification}</p><small className="reference">{refs(issue.evidence)}</small></article>)}{review.limitations.map((l,i)=><p className="muted" key={i}>{l}</p>)}</details>)}
      <h3>Assessment limits</h3><ul>{report.limitations.map(l=><li key={l}>{l}</li>)}</ul>
      <details><summary>Submitted evidence snapshot</summary><p className="meta">SHA-256 / {selected.sha256}</p>{fieldInfo.map(([key,label],i)=><section key={key}><h4>E{String(i+1).padStart(2,"0")} / {label}</h4><pre>{selected.project[key]||"(No evidence supplied)"}</pre></section>)}{selected.project.files.map((f,i)=><section key={f.name}><h4>E{String(i+6).padStart(2,"0")} / {f.name}</h4><pre>{f.content}</pre></section>)}</details>
     </>}
    </section>}
    <footer>AI COUNCIL <span>Independent review infrastructure. Human judgment stays in charge.</span></footer>
   </main>
  </div>
 </div>;
}
