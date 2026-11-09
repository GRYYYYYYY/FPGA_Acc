"""Costed export and compiled query parity, preserving graph preparation costs."""
import json,sys,subprocess,time,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from freeze_priority_family import closure
ROOT=Path(__file__).resolve().parents[2];w,i=map(int,sys.argv[1:]);out=ROOT/f'experiments/native_resume_rr_floor_cpp_w{w}_m{i}_2026-10-07';out.mkdir(exist_ok=False);start=time.perf_counter();assert sys.byteorder=='little'
prior=ROOT/f'experiments/native_resume_critical_rr_floors_w{w}_m{i}_2026-10-07';p=json.loads((prior/'protocol.json').read_text());r=json.loads((prior/'receipt.json').read_text());assert r['protocol_sha256']==sha(prior/'protocol.json') and all(sha(f)==h for f,h in p['inputs'].items());selected=set(p['selection']['selected_connection_ids'])
build=ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/receipt.json';b=json.loads(build.read_text());binary=Path(b['binary']);assert sha(binary)==b['binary_sha256'] and sha(b['source'])==b['source_sha256']
ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';graph,digest,nodes,f,rc,queries=load_endpoints(ep);queries=[q for q in queries if q['connection_id'] in selected];prepared=time.perf_counter()
initial=[rc.initial(u) for u in range(len(nodes))];limit=(1<<64)-1;assert max(initial)+len(nodes)*max(rc.increments)<limit
payload=out/'graph_queries.bin'
with payload.open('wb') as stream:
 def put(values):
  for v in values:assert 0<=v<limit;stream.write(struct.pack('<Q',v))
 put([0x5243464c4f4f5231,len(nodes),len(f['edge_ids']),len(queries)])
 for values in (f['row_offsets'],f['dest_ranks'],rc.increments,f['capacities'],initial):put(values)
 for q in queries:put([q['connection_id'],q['source'],q['sink']])
exported=time.perf_counter();protocol=dict(inputs=p['inputs'],selected_connection_ids=sorted(selected),selection=p['selection'],prior_receipt_sha256=sha(prior/'receipt.json'),build_receipt_sha256=sha(build),payload_sha256=sha(payload),graph_sha256=digest,scale=rc.scale,sources=closure([Path(__file__)]),scope='Archived own criticality query replay. Full graph XML/electrical preparation and payload export paid; snapshot acquisition, native repair and final route proof excluded. Query parity compares earlier certified floors only after compiled output; not an online workflow.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');expected={x['query']['connection_id']:x for x in r['rows']};byid={q['connection_id']:q for q in queries};runs=[];reference=None
for repeat in range(3):
 file=out/f'output_{repeat}.jsonl';tick=time.perf_counter()
 with file.open('w') as log:code=subprocess.run([str(binary),str(payload)],stdout=log,stderr=subprocess.PIPE,timeout=120)
 elapsed=time.perf_counter()-tick;assert code.returncode==0,code.stderr.decode();actual=[json.loads(line) for line in file.read_text().splitlines()];assert len(actual)==len(queries) and {x['connection_id'] for x in actual}==selected
 for x in actual:
  q=byid[x['connection_id']];assert x['minimum_integer']==expected[x['connection_id']]['minimum_integer'];edges=[f['edge_ids'][slot] for slot in x['slots']];assert rc.path(q['source'],q['sink'],edges)==x['minimum_integer']
 if reference is not None:assert actual==reference
 reference=actual;runs.append(dict(repeat=repeat,query_process_seconds=elapsed,output_sha256=sha(file),complete_integer_floor_and_path_parity=True))
assert all(sha(file)==h for file,h in p['inputs'].items()) and sha(payload)==protocol['payload_sha256'] and sha(binary)==b['binary_sha256']
receipt=dict(protocol_sha256=sha(out/'protocol.json'),connections=len(queries),preparation_seconds=prepared-start,payload_export_seconds=exported-prepared,runs=runs,trial_total_seconds=time.perf_counter()-start,scope=protocol['scope']+'; three child processes repeat immutable queries without a persistent cache; each includes binary startup/payload load/query/output. Trial total includes all three and parity verification, not a one-pass route workflow.')
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(w,receipt,flush=True)
