"""Reconcile terminal synthetic reverse RTL evidence without changing gate scope."""
from pathlib import Path
import json,hashlib,time,os
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 old=R/'work/current_research_claim_matrix_v24_20261021/matrix.json';m=json.loads(old.read_text())
 drift=[n for n,h in m['source_sha256'].items() if not (R/n).exists() or sha(R/n)!=h];assert not drift,drift
 o=R/'work/current_research_claim_matrix_v25_20261021';o.mkdir();p=R/'experiments/research_plan.json';raw=p.read_bytes();plan=json.loads(raw);(o/'plan_snapshot.json').write_bytes(raw)
 ev=['work/resident_tail_word_random_RTL_20261021/independent_random_RTL_review.json','work/resident_tail_word_random_RTL_audit_recovery_v2_20261021/review.json']
 a=json.loads((R/ev[0]).read_text());assert a['declared_calls']==2000
 for name,h in a['source_sha256'].items():assert sha(name)==h,name
 m['claims'].append(dict(id='H_REVERSE_WORD_RANDOM_RTL',gates=['G6'],claim='All2000declared synthetic reverse scalar Verilog transactions pass C postcheck and four output-bundle byte equality checks',evidence=ev,limits='Fixed seed20261021,n2–10,levels1–4;status histogram retains1183exhausted,52cutoff,245invalid,106stale,10frontier and404backend failures. Reported total13434642cycles includes all states. Not2000successful routes,representative workload RTL,independent algorithm correctness,physical timing or throughput. Original auditor wildcard failure preserved;separate v2 selects top report against frozen Tcl without resimulation.',status='supported_in_declared_scope'))
 for name in ev:m['source_sha256'][name]=sha(R/name)
 for f in [old,Path(__file__),o/'plan_snapshot.json']:m['source_sha256'][str(f.relative_to(R))]=sha(f)
 gates=[{k:g[k] for k in ['id','requirement','status']} for g in plan['gates']];assert len(gates)==8 and all(g['status']!='complete' for g in gates)
 m.update(schema='dieroute.claim_matrix.v25',recorded_ns=time.time_ns(),gates=gates,predecessor={'path':str(old.relative_to(R)),'sha256':sha(old)},scope='Original8gates open. Adds terminal2000synthetic reverse RTL evidence;historical pending observations in predecessor claims remain dated scope. No representative RTL or board result.',research_complete=False,board_result=False)
 target=o/'matrix.json';target.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');plan['current_claim_matrix']={'path':str(target.relative_to(R)),'sha256':sha(target),'status':m['status'],'research_complete':False}
 critical=R/'experiments/critical_path_20261020.md';before=critical.read_bytes();(o/'critical_path_before.md').write_bytes(before);text=before.decode().replace('work/current_research_claim_matrix_v24_20261021/matrix.json','work/current_research_claim_matrix_v25_20261021/matrix.json');text+='\nTerminal synthetic reverse RTL update: all2000declared transactions independently verified,4output bundles byte equal,13434642reported total cycles. Original auditor report-selection error and separate v2 recovery retained. Previous pending RTL notes are historical;representative real-workload RTL and all8gates remain open.\n';assert critical.read_bytes()==before;critical.write_text(text);plan['completion_critical_path']['sha256']=sha(critical)
 assert p.read_bytes()==raw;tmp=p.with_name('.research_plan_matrix25.tmp');tmp.write_text(json.dumps(plan,indent=2,ensure_ascii=False)+'\n');os.replace(tmp,p)
 review=dict(status='terminal_random_RTL_reconciled_all8gates_open',claims=len(m['claims']),direct_sources=len(m['source_sha256']),predecessor_source_drift=drift,open_gates=8,matrix_sha256=sha(target),research_complete=False);(o/'review.json').write_text(json.dumps(review,indent=2)+'\n');print(json.dumps(review))
if __name__=='__main__':main()
