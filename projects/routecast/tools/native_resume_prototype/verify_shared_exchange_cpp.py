"""Bind compiled parity to prior complete native quality evidence."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_shared_exchange_cpp_comparison_2026-10-07';out.mkdir(exist_ok=False);nv=ROOT/'experiments/native_resume_full_exchange_comparison_2026-10-07/verification.json';native=json.loads(nv.read_text());assert all(sha(f)==h for f,h in native['bindings'].items());bindings={str(nv):sha(nv),str(Path(__file__)):sha(Path(__file__))};rows=[]
for w,i in ((16,1),(32,3)):
 d=ROOT/f'experiments/native_resume_shared_exchange_cpp_w{w}_m{i}_2026-10-07';r=json.loads((d/'receipt.json').read_text());assert all(sha(f)==h for f,h in r['bindings'].items());bindings.update(r['bindings']);bindings[str(d/'receipt.json')]=sha(d/'receipt.json');ref=ROOT/f'experiments/native_resume_full_exchange_delay_0.01_w{w}_m{i}_2026-10-07';expected=json.loads((ref/'receipt.json').read_text())['rows'];actual=list(map(json.loads,(d/'output.jsonl').read_text().splitlines()));assert len(actual)==len(expected);count=0
 # CSR slot to physical EID mapping was checked in producer against immutable RR XML.
 for idx,(a,b) in enumerate(zip(actual,expected)):
  assert a['index']==idx and a['attempts']==b['attempts'];assert a['old_wire']==b['old_wire'] and a['new_wire']==b['new_wire'];assert len(a['records'])==len(b['records'])
  for x,y in zip(a['records'],b['records']):assert x['connection_id']==y['query']['connection_id'] and x['delay']==y['conditional_integer'];count+=1
 n=next(x for x in native['rows'] if x['width']==w);assert count==n['connections'] and r['all_decisions_paths_and_delays_exact'];assert n['joint_vs_matched_cold'] and n['joint_vs_unfloored_cold'];rows.append(dict(width=w,connections=count,conversion_seconds=r['conversion_seconds'],compiled_child_seconds=r['compiled_child_seconds'],total_conversion_query_parity_seconds=r['total_conversion_query_parity_seconds'],python_seconds=r['python_reference_seconds'],cpd_ns=n['cpd_ns'],wirelength=n['wirelength'],quality_by_exact_native_verified_path_parity=True))
(out/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Exact decisions and delays replay; producer exact CSR-slot/physical-EID equality binds to previous complete original-native proof. No fresh native run, durable cache, concurrent state or full-cost end-to-end gain.'),indent=2)+'\n');print(rows)
