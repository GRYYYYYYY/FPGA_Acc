"""Snapshot completed baseline/candidate1-3 arms; no full-matrix claim."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from prepared_endpoints import PreparedEndpoints
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
from feedback_scores import scores
from net_union_topology import diagnose
root=Path('experiments/frisc_pressure_candidate_matrix_2026-10-05');out=Path('experiments/frisc_pressure_union_prefix_2026-10-05');cases=[(c,a) for c in range(4) for a in (0,256)]
if out.exists():raise ValueError('fresh output required')
p=json.loads((root/'protocol.json').read_text());ep=json.loads(Path('experiments/frisc_endpoints_2026-10-05/endpoints.json').read_text());inputs={str(root/'protocol.json'):sha(root/'protocol.json'),**p['inputs_sha256']}
for c,a in cases:
 for name in (f'prediction_{c}_{a}.json',f'report_{c}_{a}.json'):inputs[str(root/name)]=sha(root/name)
assert all(sha(f)==h for f,h in inputs.items());start=time.monotonic();g=read_rr_graph(ep['inputs']['graph']['path']);frontend=PreparedEndpoints(ep['inputs']['net']['path'],ep['inputs']['graph']['path'],ep['inputs']['place']['path']);rows=[]
for c in range(4):
 e=ep if c==0 else frontend.project(Path(f'experiments/frisc_local_candidates_2026-10-05/candidate_{c}.place'))[0]
 for alpha in (0,256):
  prediction=json.loads((root/f'prediction_{c}_{alpha}.json').read_text());report=json.loads((root/f'report_{c}_{alpha}.json').read_text());assert audit(g,e,prediction)==report['report']['physical_audit'];assert scores(g,e,prediction['node_occupancy'])==report['scores'];d=diagnose(g,prediction);rows.append({'candidate_id':c,'alpha':alpha,'diagnostic':d})
assert all(sha(f)==h for f,h in inputs.items());out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());(out/'net_union_topology.py').write_text(Path('tools/net_union_topology.py').read_text());receipt={'scope':'fixed completed eight-arm prefix; full18 matrix still separate','input_sha256':inputs,'source_sha256':sha(__file__),'module_sha256':sha('tools/net_union_topology.py'),'rows':rows,'wall_s':time.monotonic()-start,'limitations':['no complete ranking claim','structural net-union checks do not certify cross-net capacity or VPR route-tree legality']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps([{'candidate_id':r['candidate_id'],'alpha':r['alpha'],**{k:v for k,v in r['diagnostic'].items() if k not in ('nets','scope')}} for r in rows]))
