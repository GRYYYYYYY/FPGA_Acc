import json,sys
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
new=R/'experiments/aes_affected_cache_full_workflow_v1_2026-10-08';old=R/'experiments/aes_workspace_full_workflow_v1_2026-10-08';bindings={str(Path(__file__)):sha(Path(__file__))};datasets=[]
for root in [old,new]:
 p=root/'verification.json';v=json.loads(p.read_text());assert v['fresh_estimates_native_full_endpoints_capacity_canonical_pass'] and all(sha(k)==x for k,x in v['bindings'].items());r=root/'receipt.json';d=json.loads(r.read_text());assert all(sha(k)==x for k,x in d['bindings'].items());bindings.update({str(p):sha(p),str(r):sha(r)});datasets.append(d['rows'])
rows=[]
for a,b in zip(*datasets):
 assert a['name']==b['name'];name=a['name']
 for file in ['seed.route','scope_partition.json','identity.jsonl','design.blif','design.net','design.place']:
  pa=old/name/file;pb=new/name/file;assert pa.read_bytes()==pb.read_bytes();bindings[str(pa)]=sha(pa);bindings[str(pb)]=sha(pb)
 for file in ['subset.json','resident/initial.json','resident/floors.json','resident/sketch.json','resident/round0.json','resident/round1.json']:
  pa=old/name/file;pb=new/name/file;assert json.loads(pa.read_text())==json.loads(pb.read_text());bindings[str(pa)]=sha(pa);bindings[str(pb)]=sha(pb)
 assert a['cpd_ns']==b['cpd_ns'] and a['wirelength']==b['wirelength'];assert a['required_connections']==b['required_connections'] and a['retained_connections']==b['retained_connections'];rows.append({'name':name,'all_model_frames_subset_seed_and_original_fixed_inputs_exact_parity':True,'native_cpd_ns':b['cpd_ns'],'native_wirelength':b['wirelength'],'original_full_seconds':a['actual_complete_workflow_seconds'],'workspace_full_seconds':b['actual_complete_workflow_seconds'],'scope':'Exact estimator/selection/seed/input and native QoR parity. Single observed full pipeline costs, not a stable statistical speed claim.'})
assert all(sha(k)==v for k,v in bindings.items());(new/'native_parity_verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n');print(rows)
