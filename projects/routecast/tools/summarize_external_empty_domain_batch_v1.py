"""Close the frozen one-round probe without changing the historical experiments."""
import hashlib,json,os
from datetime import datetime,timezone
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
C=E/'prospective_external_family_core_probe_cnf_v1_2026-10-19'
Q=E/'prospective_external_family_empty_domain_batch_v1_2026-10-19'
D=E/'prospective_external_family_empty_domain_cnf_v1_2026-10-19'
P=E/'prospective_external_family_empty_domain_provenance_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
cache={}
def sha(p):
 p=Path(p)
 if p not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
  cache[p]=h.hexdigest()
 return cache[p]
def empty_domains(c):
 neg={-v[0] for v in c['clauses'] if len(v)==1 and v[0]<0};groups={}
 for i,v in enumerate(c['variables'],1):
  if v['kind']=='CHOICE':groups.setdefault(v['key'][0],set()).add(i)
 return {n for n,vs in groups.items() if vs<=neg}
def main():
 receipts=[P/'verification.json',Q/'protocol.json',Q/'verification.json',Q/'independent_verification_v1.json',D/'verification.json',D/'independent_structure_verification_v1.json',D/'solve/verification.json',D/'supports/verification.json']
 pending=list(receipts);seen=set();bindings={str(Path(__file__).resolve()):sha(Path(__file__))}
 while pending:
  p=pending.pop()
  if p in seen:continue
  seen.add(p);d=read(p);bindings[str(p)]=sha(p)
  if not isinstance(d,dict):continue
  for name,expected in d.get('bindings',{}).items():
   target=Path(name);assert sha(target)==expected,(str(p),name)
   bindings[name]=expected
   if target.suffix=='.json':pending.append(target)
 rows=[]
 for ep in range(1,4):
  case=f'w160/episode_{ep:02d}';oldp=C/case/'encoding.json';newp=D/case/'encoding.json';old=read(oldp);new=read(newp);before=empty_domains(old);after=empty_domains(new);target={1:2381,2:5324}.get(ep)
  result=read(D/'solve'/case/'verification.json')
  rows.append(dict(case=case,initial_explicit_unit_empty_domains_before=sorted(before),initial_explicit_unit_empty_domains_after=sorted(after),repaired=sorted(before-after),newly_explicit=sorted(after-before),previous_core_NET=target,previous_core_domain_initially_empty_now=target in after if target else None,mandatory_conflicts_before=len(old['mandatory_unit_conflicts']),mandatory_conflicts_after=len(new['mandatory_unit_conflicts'])))
  bindings[str(oldp)]=sha(oldp);bindings[str(newp)]=sha(newp)
 solves=read(D/'solve/verification.json')['rows'];assert len(solves)==3 and all(r['status']=='UNSAT' and r['proof_pass'] and r['visited_nodes']==1 for r in solves)
 probe=read(Q/'verification.json')['rows'];assert sum(r['new_candidates'] for r in probe)==121
 decision=dict(status='ONE_FROZEN_ALL_EMPTY_DOMAIN_BATCH_VERIFIED_ALL3_FINITE_BANKS_STILL_UNSAT',updated_utc=datetime.now(timezone.utc).isoformat(),bindings=bindings,probe=probe,domain_diagnostics=rows,solves=[{k:r[k] for k in ('case','status','visited_nodes','proof_pass')} for r in solves],unavailable_cases_preserved=6,labels_opened=False,budgets_changed=False,promoted=False,quality_and_utility_gates_pass=False,interpretation='All 125 frozen actions executed once. 121 new complete trees and 3620 paths independently checked, two duplicates and two no-admitted outcomes retained. Initial explicit empty domains decrease 73/14/18 to 1/1/0; direct mandatory conflicts 10/0/0 to zero. Cases 1/2 still exhaust NET2381/5324. Case3 has no initial empty domain; NET5726 and NET5752 each have one option surviving initial negative units, both require unit node109534. Certified 9-clause support proves their collision. Counts are syntax-dependent, not a complete propagation metric.',methodology='All initial empty NETs avoid all foreign mandatory unit nodes; all direct conflict owners avoid each conflict separately. Actions fixed for all cases before searching, with independent reconstruction from original XML and old banks. No adaptive refill.',scope='Finite-bank capacity feasibility only. No general routing, budget-wide, ranking, native timing, quality, utility, unseen-family or hardware success claim.',next_step='Investigate budget-compatible blocker release for NET2381 and NET5324, and propagated mandatory ownership for NET5726/5752. Any new generation requires a separate frozen policy; this completed batch is not extended.')
 out=D/'research_decision_v1.json';assert not out.exists();out.write_text(json.dumps(decision,indent=2)+'\n')
 qp=Q/'research_decision_v1.json';assert not qp.exists();qp.write_text(json.dumps(dict(status=decision['status'],decision=str(out),decision_sha256=sha(out),promoted=False),indent=2)+'\n')
 checkpoint=E/'mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json';state=read(checkpoint);state['prospective_external_family_empty_domain_batch_v1']=dict(status=decision['status'],decision=str(out),decision_sha256=sha(out),updated_utc=decision['updated_utc'],promoted=False);tmp=checkpoint.with_name(checkpoint.name+'.core_probe.tmp');tmp.write_text(json.dumps(state,indent=2)+'\n');os.replace(tmp,checkpoint)
 print(json.dumps(dict(status=decision['status'],verified_binding_files=len(bindings),rows=[dict(case=r['case'],before=len(r['initial_explicit_unit_empty_domains_before']),after=len(r['initial_explicit_unit_empty_domains_after']),repaired=len(r['repaired'])) for r in rows])))
if __name__=='__main__':main()
