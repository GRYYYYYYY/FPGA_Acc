"""Original XML branch/capacity audit and route-free endpoint name alignment."""
import json,time
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha,extract
from stream_native_route_audit import audit
from audit_native_route import NET
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/bitonic_native_reference_2026-10-07';out=ROOT/'experiments/bitonic_physical_endpoints_2026-10-07';r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert r['complete'] and v['receipt_sha256']==sha(parent/'receipt.json');out.mkdir();sources=[Path(__file__),ROOT/'tools/pre_route_endpoints.py',ROOT/'tools/stream_native_route_audit.py',ROOT/'tools/audit_native_route.py'];protocol=dict(parent_receipt_sha256=sha(parent/'receipt.json'),parent_verification_sha256=sha(parent/'verification.json'),sources={str(p):sha(p) for p in sources},cohort=[4,8,16],policy='Audit everycase. Route is evaluator-only input; extractor takes ONLY net/place/graph. Match name+SOURCE+SINK multiplicities, not native numericNET ids. No changed predictor settings.');(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for row in r['rows']:
 n=row['count'];assert row['exit_code']==0 and all(sha(f)==h for f,h in row['files'].items());work=out/f'n{n}';work.mkdir();files={Path(f).name:Path(f) for f in row['files']};start=time.perf_counter();physical=audit(files['rr_graph.xml'],files['design.route']);assert physical['connections'] and physical['overflow_units']==0
 ep,mapping=extract(files['design.net'],files['design.place'],files['rr_graph.xml']);assert set(ep['inputs'])=={'net','place','graph'} and not ep['excluded_nets']
 names={}
 for line in files['design.route'].read_text().splitlines():
  match=NET.match(line)
  if match:names[int(match[1])]=match[2]
 routed=Counter((names[q['net_id']],q['source'],q['sink']) for q in physical['connections']);mapped=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);assert mapped==routed
 for name,obj in [('physical_audit.json',physical),('endpoints.json',ep),('mapping.json',mapping)]:
  (work/name).write_text(json.dumps(obj,indent=2)+'\n')
 rows.append(dict(count=n,connections=len(ep['connections']),routed_nets=physical['routed_nets'],occupied_nodes=physical['occupied_nodes'],overflow_units=0,required_distinct_arcs=physical['required_distinct_arcs'],route_free_endpoints_match_named_native_terminals=True,seconds=time.perf_counter()-start,files={str(f):sha(f) for f in work.iterdir()}));print(n,rows[-1]['connections'],'paths and endpoints audited',flush=True)
assert all(sha(f)==h for f,h in protocol['sources'].items())
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,scope='All3 native printed branch arcs/switches/tree and uniqueNET capacity audited original XML; name/SOURCE/SINK multiplicities equal independent packed/place endpoint mapping. Not bufferedRCdelay/FULLSTA closure, predictor accuracy, or total time benefit. Route labels evaluator-only; predictor endpoints contain no route input.'),indent=2)+'\n')
