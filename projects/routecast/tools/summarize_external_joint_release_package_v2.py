"""Archive the fixed atomic package experiment and independent failure ablations."""
import json,os,hashlib
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_joint_release_package_v2_2026-10-19'
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
 start=[D/'protocol.json',D/'verification.json',D/'independent_verification_v1.json',D/'failure_ablation_v1.json',E/'prospective_external_family_joint_release_package_v1_2026-10-19/implementation_failure_v1.json'];pending=list(start);seen=set();bindings={str(Path(__file__).resolve()):sha(Path(__file__))}
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
 assert all(not r['failure']['outside_alone_obstruction'] and r['failure']['fixed_root_order_independent_obstruction'] for r in ab['rows'])
 witness=[]
 for row in ab['rows']:
  details=row['failure']['masks']['outside_plus_fixed_root']['details'];assert details
  for d in details:assert d['shortest_delay'] is not None and d['shortest_delay']>d['budget']
  witness.append(dict(case=row['case'],net_id=row['failure']['net_id'],order_independent_fixed_root_budget_counterexamples=details,scope='Independent original XML shortest path under fixed root plus fixed outside mandatory ownership. Refutes this fixed package for every internal order, not alternative roots or broader conditional releases.'))
 decision=dict(status='ALL3_FIXED_ROOT_JOINT_PACKAGES_REJECTED_BY_ORDER_INDEPENDENT_BUDGET_OBSTRUCTIONS',updated_utc=datetime.now(timezone.utc).isoformat(),bindings=bindings,protocol=protocol['policy'],package_audits=a['rows'],failure_ablations=ab['rows'],fixed_root_obstructions=witness,verified_connection_paths=sum(r['connection_paths_verified'] for r in a['rows']),unavailable_cases_preserved=6,committed_packages=0,new_bank_candidates=0,labels_opened=False,budgets_changed=False,promoted=False,quality_and_utility_gates_pass=False,implementation_correction='v1 aborted on NodeView subscription during first replacement parent validation; no search conclusion or package committed. v2 uses existing get interface, same packages and NET order, original failure receipt preserved.',interpretation='All partial trees satisfy original paths, proxy budgets, parent-tree and conditional capacity ledger. Packages reject atomically on first failed NET. Outside-only mask admits every failed-NET connection; outside+fixed-root already exceeds budget for CID2004 in case1 and CID2460 in cases2/3. Thus a mere order change cannot complete these fixed roots with these outside mandatory owners. Case3 has an additional prefix-dependent failure CID2461, but CID2460 already supplies the order-independent counterexample.',next_step='Design root alternatives informed by these budget obstructions, or a separately frozen broader conditional release closure. Do not retry order sweeps or expand package quotas without a new mechanism. Keep capacity diagnostics separate from congestion ranking quality; original quality, utility, family admission, full runtime and hardware gates remain open or failed.')
 out=D/'research_decision_v1.json';assert not out.exists();out.write_text(json.dumps(decision,indent=2)+'\n');cp=E/'mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json';s=read(cp);s['prospective_external_family_joint_release_package_v2']=dict(status=decision['status'],decision=str(out),decision_sha256=sha(out),updated_utc=decision['updated_utc'],promoted=False);tmp=cp.with_name(cp.name+'.joint_package.tmp');tmp.write_text(json.dumps(s,indent=2)+'\n');os.replace(tmp,cp)
 print(json.dumps(dict(status=decision['status'],verified_binding_files=len(bindings),verified_connection_paths=decision['verified_connection_paths'],committed_packages=0)),flush=True)
if __name__=='__main__':main()
