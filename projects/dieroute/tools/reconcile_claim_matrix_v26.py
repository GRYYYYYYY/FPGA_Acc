"""Add reviewed development-parent and failed portability-cohort evidence."""
from pathlib import Path
import json, hashlib, os, time
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 old=R/'work/current_research_claim_matrix_v25_20261021/matrix.json';m=json.loads(old.read_text())
 drift=[n for n,h in m['source_sha256'].items() if not (R/n).exists() or sha(R/n)!=h];assert not drift,drift
 o=R/'work/current_research_claim_matrix_v26_20261021';o.mkdir()
 p=R/'experiments/research_plan.json';raw=p.read_bytes();plan=json.loads(raw);(o/'plan_snapshot.json').write_bytes(raw)
 parent='work/conflict_detour_seq_seed1_parent_observation_20261021/review.json';work='work/conflict_detour_seq_seed1_parent_observation_20261021/work_review.json';portable='work/full_policy_isolated_v2_terminal_review_20261021/review.json'
 a=json.loads((R/parent).read_text());assert a['bindings_reverified'] and a['parent_review']['native_legal'] and a['parent_review']['wl_cpd_nonincrease']
 b=json.loads((R/work).read_text());assert b['actual']['iterations']==28 and b['actual']['overused_resources']==0 and b['reference']['iterations']==30 and b['reference']['overused_resources']==1
 for obj in [a['parent_review'],b]:
  for n,h in obj['source_sha256'].items():assert sha(n)==h,n
 c=json.loads((R/portable).read_text());assert c['planned']==c['retained']==5 and c['joint_passes']==0
 for ref in c['verified_audit_bindings']:assert sha(ref['physical'])==ref['sha256'],ref['physical']
 for ref in c['failed_stage_logs']:assert sha(ref['source'])==ref['sha256'],ref['source']
 m['claims'].extend([
 dict(id='DEVELOPMENT_SEQ1_PARENT_CAPACITY_REPAIR',gates=['G3','G4'],claim='Separate conflict-detour development seq_seed1 parent resolves original capacity failure and independently passes native wirelength/CPD nonincrease',evidence=[parent,work],limits='Parent only;28iterations,WL19055vs19170,CPD10.5655vs10.6492ns. Expanded7157887243vs6817799382 and2508extra capacity searches. Changed algorithm budget,exposed development case;original30iteration failure retained. Other first-four parents include two quality failures. Not full cohort,full policy,blind heldout or acceleration.',status='supported_in_declared_scope'),
 dict(id='ISOLATED_FULL_POLICY_V2_ALL_FIVE_ERRORS',gates=['G8'],claim='Independent isolated v2 cohort review retains all five missing-runtime-supervisor execution failures and zero successful full-policy reproductions',evidence=[portable],limits='All five fail at wirelength stage001 native preparation before full candidate native validation. Audit return0 means complete failure accounting,not successful reproduction.168audit bindings verified. Separate v3 supplements known dependencies but remains unproven;no portability closure.',status='supported_in_declared_scope')])
 for n in [parent,work,portable]:m['source_sha256'][n]=sha(R/n)
 for f in [old,Path(__file__),o/'plan_snapshot.json']:m['source_sha256'][str(f.relative_to(R))]=sha(f)
 gates=[{k:g[k] for k in ['id','requirement','status']} for g in plan['gates']];assert len(gates)==8 and all(g['status']!='complete' for g in gates)
 m.update(schema='dieroute.claim_matrix.v26',recorded_ns=time.time_ns(),gates=gates,predecessor={'path':str(old.relative_to(R)),'sha256':sha(old)},scope='All original8gates open. Adds one new-algorithm parent repair and independent all-five isolated-v2 failure accounting. No full development cohort or artifact portability closure.',research_complete=False,board_result=False)
 target=o/'matrix.json';target.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');plan['current_claim_matrix']={'path':str(target.relative_to(R)),'sha256':sha(target),'status':m['status'],'research_complete':False}
 critical=R/'experiments/critical_path_20261020.md';before=critical.read_bytes();(o/'critical_path_before.md').write_bytes(before);text=before.decode().replace('work/current_research_claim_matrix_v25_20261021/matrix.json','work/current_research_claim_matrix_v26_20261021/matrix.json');text+='\nClaim matrix v26 records the independently reviewed seq_seed1 development parent and all five isolated-v2 execution failures. Historical pending notes remain dated observations;v3 is a separate cohort,not replacement of v2 failures. All eight gates remain open.\n';assert critical.read_bytes()==before;critical.write_text(text);plan['completion_critical_path']['sha256']=sha(critical)
 assert p.read_bytes()==raw;tmp=p.with_name('.research_plan_matrix26.tmp');tmp.write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n');os.replace(tmp,p)
 review=dict(status='development_parent_and_failed_portability_cohort_reconciled',claims=len(m['claims']),direct_sources=len(m['source_sha256']),predecessor_source_drift=drift,open_gates=8,matrix_sha256=sha(target),research_complete=False);(o/'review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps(review))
if __name__=='__main__':main()
