export type EvidenceFile = {name:string;content:string};
export type Project = {title:string;research_question:string;findings:string;methods:string;results:string;limitations:string;files:EvidenceFile[]};
export type Ref = {evidence_id:string;start_line:number;end_line:number};
export type Issue = {title:string;severity:"Critical"|"Moderate"|"Nitpick";claim_status:string;detail:string;consequence:string;improvement:string;verification:string;evidence:Ref[]};
export type Review = {reviewer:string;strengths:{detail:string;evidence:Ref[]}[];issues:Issue[];limitations:string[]};
export type Report = {simulated:boolean;summary:string;model:string;prompt_version:string;reviewers:Review[];priorities:{title:string;severity:string;reviewers:string[];issues:Issue[];disagreement:boolean}[];limitations:string[]};
export type Entry = {id:string;title?:string;created_at:string;status:"queued"|"running"|"completed"|"incomplete";completed_reviewers:number;error:string|null};
export type Assessment = Entry & {project:Project;sha256:string;report:Report|null};
