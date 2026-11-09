"""Archive the fixed atomic package experiment and independent failure ablations."""
import json,os,hashlib
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_budget_aware_joint_package_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
cache={}
def sha(p):
 p=Path(p)
 if p not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
  cache[p]=h.hexdigest()
 return cache[p]
def main():
 start=[D/'protocol.json',D/'verification.json',D/'independent_verification_v1.json',D/'failure_ablation_v1.json',D/'obstruction_repair_witness_v1.json'];pending=list(start);seen=set();bindings={str(Path(__file__).resolve()):sha(Path(__file__))}
 while pending:
  p=pending.pop()
  if p in seen:continue
  seen.add(p);d=read(p);bindings[str(p)]=sha(p)
  if not isinstance(d,dict):continue
  for q,h in d.get('bindings',{}).items():
   assert sha(q)==h,(str(p),q);bindings[q]=h
   if Path(q).suffix=='.json':pending.append(Path(q))
 a=read(D/'independent_verification_v1.json');ab=read(D/'failure_ablation_v1.json');raw=read(D/'verification.json');protocol=read(D/'protocol.json');assert len(a['rows'])==len(ab['rows'])==len(raw['rows'])==3
 assert [r['package_NETs'] for r in a['rows']]==[258,243,253]
 assert all(not r['package_accepted'] for r in a['rows']) and all(not r['committed'] and r['status']=='PACKAGE_SEARCH_FAILED_NO_COMMIT' for r in raw['rows'])
 assert [r['failure']['fixed_pair_order_independent_obstruction'] for r in ab['rows']]==[True,False,True];assert all(not r['failure']['masks']['outside_only']['failed_CIDs'] for r in ab['rows'])
 witness=[]
 for row in ab['rows']:
  details=row['failure']['masks']['outside_plus_reserved_and_regenerated_root']['details']
  if not details:continue
  for d in details:assert d['shortest_delay'] is not None and d['shortest_delay']>d['budget']
  witness.append(dict(case=row['case'],net_id=row['failure']['net_id'],order_independent_fixed_root_budget_counterexamples=details,scope='Independent original XML shortest path under fixed root plus fixed outside mandatory ownership. Refutes this fixed package for every internal order, not alternative roots or broader conditional releases.'))
 decision=dict(status='ALL3_BUDGET_AWARE_PACKAGES_REJECTED_PRIOR_OBSTRUCTIONS_REPAIRED_NEW_FAILURES_DISTINGUISHED',updated_utc=datetime.now(timezone.utc).isoformat(),bindings=bindings,protocol=protocol['policy'],package_audits=a['rows'],failure_ablations=ab['rows'],fixed_root_obstructions=witness,verified_connection_paths=sum(r['connection_paths_verified'] for r in a['rows']),unavailable_cases_preserved=6,committed_packages=0,new_bank_candidates=0,labels_opened=False,budgets_changed=False,promoted=False,quality_and_utility_gates_pass=False,obstruction_repair_witnesses=read(D/'obstruction_repair_witness_v1.json')['rows'],methodology='One independently diagnosed prior failed NET reserved first; NET2 regenerated once against that complete tree, fixed outside mandatory owners and original union mask. Original package membership, remaining NET order and budgets fixed before all searches. No alternative order or mask retries, no partial commits.',interpretation='All three prior budget obstructions have explicit feasible paths under the new compatible root/reserved pair. CID2004 becomes545800003 with budget1000000000; CID2460 becomes753700006 with budget1130550009 in cases2/3, all units1e-18 seconds. Full packages still fail:19/24/24 selected conditional trees, failed NET287/388/388. Five fixed causal masks distinguish cases: cases1/3 new root alone already induces budget violations at CID2460/2751, but case2 new root plus reserved tree admits all failed-NET connections and only later prefix causes CID2751 failure. Do not claim order-independent fixed-pair infeasibility for case2.',next_step='Design multi-constraint root generation for cases1/3 and conditional predecessor rollback for case2. Inventory complete roots and prefix blocking owners using pre-label paths and original budgets; freeze a mechanism before another experiment, rather than arbitrary order, root or package quota sweeps. Keep capacity diagnostics separate from original forecast quality, native utility, strict family, full runtime and hardware gates.')
 out=D/'research_decision_v1.json';assert not out.exists();out.write_text(json.dumps(decision,indent=2)+'\n');cp=E/'mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json';s=read(cp);s['prospective_external_family_budget_aware_joint_package_v1']=dict(status=decision['status'],decision=str(out),decision_sha256=sha(out),updated_utc=decision['updated_utc'],promoted=False);tmp=cp.with_name(cp.name+'.joint_package.tmp');tmp.write_text(json.dumps(s,indent=2)+'\n');os.replace(tmp,cp)
 print(json.dumps(dict(status=decision['status'],verified_binding_files=len(bindings),verified_connection_paths=decision['verified_connection_paths'],committed_packages=0)),flush=True)
if __name__=='__main__':main()
