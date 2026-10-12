export type Criterion = { type: 'contains'|'exact'|'required_keywords'|'forbidden_content'; value: string|string[] }
export type TestCase = { id:string; name:string; input:string; expected_behavior:string; evaluation_criteria:Criterion[] }
export type Suite = { id:string; name:string; description:string; cases:TestCase[]; is_seeded:boolean; created_at:string }
export type CaseResult = { case_id:string; case_name:string; input:string; expected_behavior:string; actual_response:string; passed:boolean; reason:string; latency_ms:number }
export type Metrics = { total:number; passed:number; failed:number; pass_rate:number; average_latency_ms:number }
export type Run = { id:string; suite_id:string; suite_name:string; source:'execution'|'seeded'; created_at:string; metrics:Metrics; results:CaseResult[] }
export type Comparison = { baseline_run_id:string; candidate_run_id:string; fixed:string[]; regressions:string[]; unchanged_passed:string[]; unchanged_failed:string[] }
