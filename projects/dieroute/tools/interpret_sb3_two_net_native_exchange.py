"""Bind native validations to repaired trees and interpret joint quality."""
import csv,hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb3_ex5p_two_net_native_validation_v2_20261015'
def main():
 refs={}
 def sha(f):
  f=Path(f);h=hashlib.sha256()
  with f.open('rb') as stream:
   for b in iter(lambda:stream.read(1048576),b''):h.update(b)
  refs[str(f)]=h.hexdigest();return h.hexdigest()
 def load(f):sha(f);return json.loads(Path(f).read_text())
 def trees(f):
  sha(f);answer={}
  for row in csv.DictReader(Path(f).open()):answer.setdefault(int(row['net_id']),set()).add((int(row['parent']),int(row['child'])))
  return answer
 protocol=load(P/'protocol.json');result=load(P/'result.json');c=protocol['case']
 for f,h in protocol['source_sha256'].items():assert sha(f)==h,f
 upstream=R/'work/sb3_ex5p_two_net_exchange_v2_20261015'
 assert sha(upstream/'result.json')==result['upstream_result_sha256']
 assert sha(upstream/'independent_audit.json')==result['upstream_audit_sha256']
 topology=Path(c['topology_prefix']+'.node_die');die=[v[0] for v in struct.iter_unpack('<H',topology.read_bytes())];sha(topology)
 parent_protocol=load(R/'work/sb3_fixed_feedback_pair_20261015/protocol.json');assert refs[str(topology)]==parent_protocol['source_sha256'][str(topology)]
 def crossings(mapping):return sum(die[u]!=die[v] for edges in mapping.values() for u,v in edges)
 rows=[]
 for trial in result['outcomes']:
  label=trial['label'];arm=label.split('_owner')[0];d=P/label
  parent=R/'work/sb3_fixed_feedback_pair_20261015/native_runs'/('ex5p_'+arm+'_0')
  original=trees(parent/'route.route_trees.csv');candidate=trees(d/'route.route_trees.csv')
  assert candidate.keys()==original.keys()
  modified={n for n in candidate if candidate[n]!=original[n]}
  assert modified<={138,trial['displaced_net']},modified
  quality=load(d/'native_validation/validation.json');before=load(parent/'native_validation/validation.json')
  assert quality==trial['validation'] and trial['validation_returncode']==0 and quality['legal']
  assert sha(d/'native.route')==trial['native_route_sha256']==quality['inputs']['route_sha256']
  assert sha(d/'route.route_trees.csv')==trial['tree_sha256']
  for key,path in [('vpr',protocol['vpr']),('arch',Path(c['native_case'])/'architecture.xml'),('rr_graph',Path(c['native_case'])/'rr_graph.xml')]:assert sha(path)==quality['inputs'][key+'_sha256']
  old_cross,new_cross=crossings(original),crossings(candidate)
  baseline_gate=quality['total_wirelength']<=c['baseline_wirelength'] and quality['critical_path_delay_ns']<=c['baseline_cpd_ns']
  rows.append(dict(label=label,legal=True,modified_nets=sorted(modified),native_wirelength=quality['total_wirelength'],native_cpd_ns=quality['critical_path_delay_ns'],
   wirelength_delta_from_parent=quality['total_wirelength']-before['total_wirelength'],cpd_delta_from_parent_ns=quality['critical_path_delay_ns']-before['critical_path_delay_ns'],
   parent_crossings=old_cross,candidate_crossings=new_cross,joint_WL_CPD_baseline_pass=baseline_gate))
 assert len(rows)==3 and all(not v['joint_WL_CPD_baseline_pass'] for v in rows)
 sha(Path(__file__).resolve())
 report=dict(status='three_legal_native_exchanges_improve_parent_CPD_but_fail_joint_baseline_quality',outcomes=rows,source_sha256=refs,
  adopted=False,research_complete=False,scope='Posterior ex5p diagnostic, one route per candidate, exact frozen source-bound VPR validation. Only selected2nets may differ; all other611nets preserved. No general policy, repeated/heldout result, global quality success or physical performance claim.')
 with (P/'interpretation.json').open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
 print(json.dumps(dict(status=report['status'],outcomes=rows)))
if __name__=='__main__':main()
