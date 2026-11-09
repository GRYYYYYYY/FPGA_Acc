"""Post-screen diagnosis only: fixed target ties versus actual occupied support."""
import json,hashlib
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];S=R/'experiments/prince_full_resource_history_v1_2026-10-20';D=R/'experiments/prince_history_rank_split_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);v=load(S/'verification.json');rows=[];bindings={str(S/'verification.json'):sha(S/'verification.json'),str(Path(__file__)):sha(__file__)}
 for row in v['rows']:
  if row['status']!='SCORED':rows.append(dict(case=row['case'],status=row['status']));continue
  c=row['case'];sp=R/'experiments/prince_feedback_quality_v1_2026-10-20'/c/'specification.json';spec=load(sp);label=Path(spec['label_physical_audit']);truth={int(n):y for n,y in load(label)['node_occupancy'].items()};fp=S/c/'input_features.jsonl';features=list(map(json.loads,fp.open()));cells=defaultdict(list)
  for x in features:cells[x['B'],x['H']].append(x['id'])
  counts={f'{b},{h}':dict(resources=len(ns),occupied=sum(truth.get(n,0) for n in ns)) for (b,h),ns in sorted(cells.items())};methods={};k=row['metrics']['BH']['resource']['k'];target=set(row['metrics']['BH']['resource']['truth_top_k']);domain={x['id'] for x in features};assert target==set(sorted(n for n in domain if truth.get(n,0))[:k]);assert all(truth.get(n,0) in [0,1] for n in domain)
  for name in ['clipped_ready','BH']:
   m=row['metrics'][name]['resource'];selected=set(m['prediction_top_k']);assert len(selected)==k;cell_selected=Counter((x['B'],x['H']) for x in features if x['id'] in selected);actual=sum(truth.get(n,0) for n in selected);fixed=len(selected&target);assert fixed==m['top_k_hits'];missed_occupied=actual-fixed
   # Binary truth has many equally maximal resources; these extrema change ONLY truth tie selection.
   total_ones=sum(truth.get(n,0) for n in domain);low=max(0,k-(total_ones-actual));high=min(k,actual)
   assert low<=fixed<=high
   methods[name]=dict(fixed_target_hits=fixed,actual_final_occupied_selected=actual,occupied_outside_fixed_target=missed_occupied,actual_occupied_precision=actual/k,truth_tie_possible_hits=[low,high],selected_cells={f'{b},{h}':n for (b,h),n in sorted(cell_selected.items())})
  selected0=set(row['metrics']['clipped_ready']['resource']['prediction_top_k']);selected1=set(row['metrics']['BH']['resource']['prediction_top_k']);removed=selected0-selected1;added=selected1-selected0
  def subset(ns):return dict(resources=len(ns),fixed_target_hits=len(ns&target),actual_final_occupied=sum(truth.get(n,0) for n in ns))
  rows.append(dict(case=c,status='DIAGNOSED',cells=counts,methods=methods,removed=subset(removed),added=subset(added),resource_spearman_delta=row['metrics']['BH']['resource']['spearman']-row['metrics']['clipped_ready']['resource']['spearman']))
  for p in [sp,label,fp]:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items())
 result=dict(status='FIXED_TARGET_TIE_AND_ACTUAL_SUPPORT_DIAGNOSED',rows=rows,bindings=bindings,scope='Post-screen exposed diagnosis only. Actual occupied precision and truth-tie extrema are NOT replacement metrics or admissible gate changes. Original full9 gate remains false.',full9_gate=False)
 with (D/'verification.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 for r in rows:
  if r['status']=='DIAGNOSED':print(r['case'],[(n,m['fixed_target_hits'],m['actual_final_occupied_selected']) for n,m in r['methods'].items()],r['resource_spearman_delta'])
if __name__=='__main__':main()
