"""Complete fixed-case model output comparison, without target routing labels."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def main():
 root=R/'experiments/mmc_restart_present_schedule_v1_2026-10-18';rows=[];bindings={str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
 for case in ['case_01','case_02','case_03']:
  original=R/f'experiments/mmc_multiplacement_models_v1_2026-10-18/{case}/feedback_on/native_retained/sketch.json';new=root/case/'sketch.json';warm=R/f'experiments/mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained/verification.json'
  a=json.loads(original.read_text());b=json.loads(new.read_text());w=json.loads(warm.read_text());old={x['connection_id']:x for x in a['records']};current={x['connection_id']:x for x in b['records']};assert set(old)==set(current) and len(old)==115572
  changed=[cid for cid in old if old[cid]['answer']['physical_edge_ids']!=current[cid]['answer']['physical_edge_ids']];nets={current[c]['net_id'] for c in changed};assert nets<=set(w['dirty_nets'])
  la={int(n):v for n,v in a['ledger'].items()};lb={int(n):v for n,v in b['ledger'].items()};different=[n for n in la.keys()|lb.keys() if la.get(n,0)!=lb.get(n,0)]
  rows.append(dict(case=case,changed_CIDs=len(changed),changed_NETs=len(nets),changed_ledger_nodes=len(different),ledger_absolute_difference=sum(abs(la.get(n,0)-lb.get(n,0)) for n in different),original_overflow=a['overflow_units'],restart_schedule_overflow=b['overflow_units'],all_changed_NETs_inside_original_endpoint_closure=True))
  for p in [original,new,warm]:bindings[str(p)]=sha(p)
 out=root/'fixed_case_output_comparison_v1.json';out.open('x').write(json.dumps(dict(status='all3_complete_output_differences_measured',bindings=bindings,cases=rows,scope='Read-only prediction comparison; no target cold labels, resource-type filtering, accuracy inference, parameter choice, or causal mechanism claim.'),indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
