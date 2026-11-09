"""Track all independently admitted coupled escapes into final model paths."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def paths(records):return {x['connection_id']:tuple(x['answer']['physical_edge_ids']) for x in records}
def main():
 root=R/'experiments/mmc_multi_NET_atomic_pair_v1_2026-10-18';ap=root/'independent_audits/group_verification_v1.json';audit=json.loads(ap.read_text());assert audit['all3_frames_and_complete_group_events_pass'];bindings={str(ap):sha(ap),str(Path(__file__).resolve()):sha(Path(__file__).resolve())};rows=[]
 for case in ['case_01','case_02','case_03']:
  rp=root/case/'receipt.json';sp=root/case/'sketch.json';ip=root/case/'initial.json'
  for p in [rp,sp,ip]:assert audit['bindings'][str(p)]==sha(p);bindings[str(p)]=sha(p)
  receipt=json.loads(rp.read_text());final=paths(json.loads(sp.read_text())['records']);state={}
  for rec in json.loads(ip.read_text())['records']:state.setdefault(rec['net_id'],[]).append(rec)
  observed=0;case_rows=[]
  for roundrow in receipt['rounds']:
   for event in roundrow['events']:
    if not event['admission']['accepted']:continue
    candidate={int(n):records for n,records in event['candidate_records'].items()};positive=[int(n) for n,v in event['standalone_overflow_deltas'].items() if v>0]
    if positive:
     old=paths([x for n in candidate for x in state[n]]);new=paths([x for rs in candidate.values() for x in rs]);changed={cid for cid in new if new[cid]!=old[cid]};assert changed
     kept=sorted(cid for cid in changed if final[cid]==new[cid]);restored=sorted(cid for cid in changed if final[cid]==old[cid]);other=sorted(changed-set(kept)-set(restored));assert len(kept)+len(restored)+len(other)==len(changed)
     case_rows.append(dict(case=case,round_index=roundrow['round_index'],group_index=event['group_index'],NETs=event['NETs'],positive_standalone_NETs=positive,group_overflow_delta=event['admission']['prospective_overflow_delta'],group_objective_delta=event['admission']['objective_delta'],changed_CIDs=len(changed),escape_candidate_paths_kept_in_final=len(kept),pre_escape_paths_restored_in_final=len(restored),other_final_paths=len(other),changed_CID_ids=sorted(changed),kept_CID_ids=kept,restored_CID_ids=restored,other_final_CID_ids=other));observed+=1
    state.update(candidate)
  assert paths([x for rs in state.values() for x in rs])==final;cert=Path(next(x for x in audit['cases'] if x['case']==case)['events']);v=json.loads(cert.read_text());assert observed==v['accepted_groups_with_positive_standalone_NET'];rows.extend(case_rows)
 assert len(rows)==6;out=root/'escape_lineage_diagnostic_v1.json';out.open('x').write(json.dumps(dict(status='all6_verified_escape_groups_final_path_lineage_complete',bindings=bindings,events=rows,scope='Complete descriptive lineage of every certified accepted group with a positive standalone NET delta. No native label read, no candidate filtering. Survival does not establish causal prediction gain, objective necessity, or counterfactual outcome without this event.'),indent=2)+'\n');print(json.dumps([{k:v for k,v in x.items() if not k.endswith('_ids')} for x in rows],indent=2),flush=True)
if __name__=='__main__':main()
