"""Authenticated source data substitution; never changes search/admission policy."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ARMS={'source_history_only','source_post_STA_only','source_history_and_post_STA'}
def load(endpoint,directory,arm,initialized):
 if arm not in ARMS:raise ValueError('unknown fixed source-input arm')
 directory=Path(directory).resolve();proof=directory/'verification.json';audit=directory/'independent_verification_v1.json';p=json.loads(proof.read_text());v=json.loads(audit.read_text());assert v['status']=='source_history_and_post_STA_payload_and_all115572_target_physical_identities_verified';assert v['bindings'][str(proof)]==sha(proof);assert all(sha(k)==h for k,h in {**p['bindings'],**v['bindings']}.items());assert Path(p['endpoint']).resolve()==Path(endpoint).resolve();ep=json.loads(Path(endpoint).read_text());assert ep['graph_sha256']==p['graph_sha256'] and p['model_present_factor']==1
 rows={r['connection_id']:r for r in json.loads(Path(p['post_STA_criticality_file']).read_text())};assert rows.keys()==initialized.keys()
 for cid,row in rows.items():
  assert all(row[k]==initialized[cid][k] for k in ['connection_id','net','local_sink_pin','global_pin','source_rr','target_rr'])
 effective=rows if arm!='source_history_only' else initialized;history={int(n):v for n,v in json.loads(Path(p['history_file']).read_text()).items()} if arm!='source_post_STA_only' else {};assert all(type(v) is int and v>0 for v in history.values())
 return effective,history,{**p['bindings'],**v['bindings'],str(proof):sha(proof),str(audit):sha(audit)}
