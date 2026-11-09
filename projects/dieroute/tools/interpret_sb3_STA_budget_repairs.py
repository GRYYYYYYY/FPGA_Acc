"""Bind all distinct slack-budget native validations and retain negative QoR."""
import csv,hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_STA_budget_repair_native_20261015'
def main():
 refs={}
 def sha(path):
  path=Path(path);h=hashlib.sha256()
  with path.open('rb') as stream:
   for b in iter(lambda:stream.read(1048576),b''):h.update(b)
  refs[str(path)]=h.hexdigest();return h.hexdigest()
 def load(path):sha(path);return json.loads(Path(path).read_text())
 def tree(path):
  sha(path);result={}
  for v in csv.DictReader(Path(path).open()):result.setdefault(int(v['net_id']),set()).add((int(v['parent']),int(v['child'])))
  return result
 result=load(P/'result.json')
 for f,h in result['source_sha256'].items():assert sha(f)==h,f
 base=R/'work/sb3_ex5p_two_net_native_validation_v2_20261015';protocol=load(base/'protocol.json');case=protocol['case'];prior=load(base/'result.json')
 topo=Path(case['topology_prefix']+'.node_die');die=[v[0] for v in struct.iter_unpack('<H',topo.read_bytes())];sha(topo)
 def crosses(t):return sum(die[u]!=die[v] for values in t.values() for u,v in values)
 rows=[]
 for row in result['outcomes']:
  if not row['complete'] or row['duplicate_canonical_tree']:continue
  label=row['native_evidence'];d=P/label;validation=load(d/'native_validation/validation.json');assert validation==row['native_quality'] and validation['legal']
  assert sha(d/'native.route')==validation['inputs']['route_sha256']
  candidate=tree(d/'route.route_trees.csv');original=tree(base/row['parent_trial']/'route.route_trees.csv');assert candidate.keys()==original.keys()
  modified={n for n in candidate if candidate[n]!=original[n]};net=int(row['parent_trial'].split('_owner')[1]);assert modified<={net}
  previous=next(v['validation'] for v in prior['outcomes'] if v['label']==row['parent_trial'])
  joint=validation['total_wirelength']<=case['baseline_wirelength'] and validation['critical_path_delay_ns']<=case['baseline_cpd_ns']
  rows.append(dict(label=label,parent_trial=row['parent_trial'],legal=True,wirelength=validation['total_wirelength'],cpd_ns=validation['critical_path_delay_ns'],
   wirelength_delta_from_exchange=validation['total_wirelength']-previous['total_wirelength'],cpd_delta_from_exchange_ns=validation['critical_path_delay_ns']-previous['critical_path_delay_ns'],
   modified_nets=sorted(modified),crossings=crosses(candidate),joint_baseline_pass=joint))
 assert len(result['outcomes'])==14 and len(rows)==result['distinct_native_runs']==6
 assert all(not v['joint_baseline_pass'] for v in rows)
 sha(Path(__file__).resolve());report=dict(status='14STA_budget_orders6distinct_legal_native_routes_all_fail_joint_baseline',outcomes=rows,source_sha256=refs,adopted=False,research_complete=False,
  scope='All orders retained; deduplication only by identical canonical tree. Only displaced net may differ from prior exchange; target/other612nets preserved. CPD/WL are native, not packed proxies. Posterior ex5p one route per order, no general policy/repeats/heldout or board claim.')
 with (P/'interpretation.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
 print(json.dumps(dict(status=report['status'],outcomes=rows)))
if __name__=='__main__':main()
