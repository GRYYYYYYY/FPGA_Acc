"""Strict exact-endpoint factory, no legacy family/path/graph fallback."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from fixed_nominal_timing_feedback_constants_v3 import FixedNominalTimingFeedback
from zero_rc_budget_certificate_graph_v1 import load_graph
R=Path(__file__).resolve().parents[1]
def create(endpoint,manifest=None):
 mp=Path(manifest) if manifest else R/'experiments/wbuart_feedback_factory_v1_2026-10-20/manifest.json';m=json.loads(mp.read_text());ep=Path(endpoint).resolve()
 if m.get('schema')!='WBUART_FIXED_NOMINAL_FEEDBACK_FACTORY_V1':raise ValueError('factory schema')
 if not all(sha(p)==h for p,h in m['bindings'].items()):raise ValueError('factory implementation/proof drift')
 rows=[r for r in m['rows'] if Path(r['endpoint']).resolve()==ep]
 if len(rows)!=1:raise ValueError('endpoint not admitted, no fallback')
 r=rows[0];data=json.loads(ep.read_text())
 if sha(ep)!=r['endpoint_sha256'] or data['graph_sha256']!=r['graph_sha256'] or sha(r['graph'])!=r['graph_sha256']:raise ValueError('endpoint/graph epoch mismatch')
 if not all(sha(p)==h for p,h in r['bindings'].items()):raise ValueError('current frame dependency drift')
 initial=json.loads(Path(r['initial']).read_text());queries={q['connection_id']:q for q in data['connections']}
 if len(queries)!=2493 or {a['connection_id'] for a in initial}!=set(queries):raise ValueError('CID domain')
 for a in initial:
  q=queries[a['connection_id']]
  if (a['full_connection_id'],a['endpoint_net_id'],a['source_rr'],a['target_rr'])!=(q['full_connection_id'],q['net_id'],q['source'],q['sink']):raise ValueError('CID provenance or identity')
 model=FixedNominalTimingFeedback(Path(r['baseline']),Path(r['components']),json.loads(Path(r['mapping']).read_text()),Path(r['baseline'])/'timing_atoms.tsv',initial,load_graph(r['graph']));bindings={**m['bindings'],**r['bindings'],str(mp.resolve()):sha(mp)}
 return model,bindings
