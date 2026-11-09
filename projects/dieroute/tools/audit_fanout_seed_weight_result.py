"""Review the completed fixed fanout/serial seed-weight comparison."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
p=root/'work/rr_fanout_seed_weight_variant_v3_20261015'
sources={}
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1048576),b''):h.update(block)
 return h.hexdigest()
def read(path):
 sources[str(path)]=sha(path)
 return json.loads(path.read_text())
r=read(p/'native_result.json');assert r['status']=='ten_native_fanout_seed_weight_runs_and_independent_audits_complete'
for name,digest in r['source_sha256'].items():assert sha(Path(name))==digest,name
protocol=read(p/'native_protocol.json')
for name,digest in protocol['source_sha256'].items():assert sha(Path(name))==digest,name
parent=root/'work/rr_fanout_net_order_variant_20261015/native_runs/fanout_serial_0'
parent_files={f.name:f for f in parent.glob('route.*')}
counts={};checks=0
for arm,weight in [('weight128',128),('weight256',256)]:
 previous=None
 for i in range(5):
  d=p/f'native_runs/{arm}_{i}'
  counters=read(d/'route.json');assert counters['legal'] and counters['route_tree_timing_weight_q']==weight
  counters.pop('wall_ms')
  files={f.name:f for f in d.glob('route.*')}
  fingerprint={k:sha(f) for k,f in files.items() if k!='route.json'}
  if previous is not None:assert previous==(counters,fingerprint)
  previous=(counters,fingerprint)
  a=read(d/'dispatch_resource_replay_audit.json');assert a['cpu_legal'] and a['final_resources_and_costs_byte_equivalent']
  if weight==128:
   assert files.keys()==parent_files.keys()
   for k,f in files.items():
    if k=='route.json':
     q=json.loads(parent_files[k].read_text());q.pop('wall_ms');assert q==counters
    else:assert sha(parent_files[k])==fingerprint[k],k
    checks+=1
 q=r['outcomes'][arm]['native_qor'];assert q['legal'] and q['vpr_exit_status']==0
 assert (q['baseline_wirelength'],q['baseline_cpd_ns'])==(9664,9.60037)
 counts[arm]=dict(repeats=5,wirelength=q['total_wirelength'],cpd_ns=q['critical_path_delay_ns'],joint_quality_pass=q['total_wirelength']<=9664 and q['critical_path_delay_ns']<=9.60037)
assert not any(v['joint_quality_pass'] for v in counts.values())
sources[str(Path(__file__).resolve())]=sha(Path(__file__).resolve())
result=dict(status='ten_native_seed_weight_runs_reviewed_joint_quality_failed',outcomes=counts,control_parent_artifact_checks=checks,verified_result_references=len(r['source_sha256']),verified_protocol_inputs=len(protocol['source_sha256']),source_sha256=sources,adopted=False,scope='Five runs per arm deterministic; native checks one per arm, repeat artifacts verified. Correct-weight dispatch/resource/seed replay and producer evidence hashes checked. Ex5p development interaction only; no universal weight conclusion, complete VPR equivalence or physical performance claim.',board_result=False,research_complete=False)
with (p/'independent_audit.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps(dict(status=result['status'],outcomes=counts,control_parent_artifact_checks=checks)))
