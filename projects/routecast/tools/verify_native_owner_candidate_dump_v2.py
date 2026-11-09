"""Audit exported post-sync native physical paths and all original target budgets."""
import json,re
from collections import Counter
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from buffered_rc_node_classes import read
from stream_native_route_audit_cached import audit
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_owner_candidate_reload_v2_2026-10-08';p=json.loads((D/'protocol.json').read_text());r=json.loads((D/'receipt.json').read_text());assert r['exit_code']==0 and sha(D/'protocol.json')==r['protocol_sha256'] and all(sha(f)==h for f,h in p['inputs'].items())
dump=D/'reconciled.route';assert sha(dump)==r['files'][str(dump)]
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);ep=json.loads(Path(case['target']).read_text());graph=Path(ep['inputs']['graph']['path']);budget=Path(case['budget']);b=json.loads(budget.read_text());ids,classes,switches,digest=read(graph);assert digest==ep['graph_sha256']
physical=audit(graph,dump);assert physical['overflow_units']==0
paths={}
for name,branches in physical_paths(dump).items():
 for path in branches:
  key=name,path[0][0],path[-1][0];assert key not in paths;paths[key]=path
state=json.loads((R/'experiments/raw_route_native_owner_candidate_v2_2026-10-08/receipt.json').read_text())['state'];rows=[];changed=[];violations=[]
for q in ep['connections']:
 cid=q['connection_id'];path=paths[ep['net_names'][str(q['net_id'])],q['source'],q['sink']];nr,nc=classes[ids[q['source']]];delay=nr*nc/2
 for dst,s in path[1:]:nr,nc=classes[ids[dst]];sr,td=switches[s];delay+=(sr+nr/2)*nc+td
 limit=Fraction(b['budgets_ns'].get(str(cid),b['default_budget_ns']));unchanged=[list(x) for x in path]==state[str(cid)]
 row=dict(connection_id=cid,delay_seconds=str(delay),budget_ns=str(limit),budget_pass=delay*10**9<=limit,model_path_unchanged=unchanged);rows.append(row)
 if not unchanged:changed.append(cid)
 if not row['budget_pass']:violations.append(cid)
assert len(rows)==len(paths)==1929
log=(D/'reload.log').read_text();m=int(re.findall(r'Found (\d+) mismatches',log)[-1]);f=int(re.findall(r'Fixed (\d+) routing traces',log)[-1])
bindings={str(x):sha(x) for x in (D/'receipt.json',D/'protocol.json',dump,D/'reload.log',graph,budget,Path(case['target']),R/'experiments/raw_route_native_owner_candidate_v2_2026-10-08/receipt.json',Path(__file__),R/'tools/stream_native_route_audit_cached.py',R/'tools/buffered_rc_node_classes.py')};assert all(sha(x)==h for x,h in bindings.items())
report=dict(bindings=bindings,connections=1929,physical=physical,changed_physical_connection_ids=changed,budget_violation_connection_ids=violations,rows=rows,pin_mismatches=m,trace_fixups=f,scope='Post-sync internal route export verified physically and against original exact buffered RC budgets. Nonzero packing/pin reconciliation preserved; no zero-fixup gate or packed HDL equivalence/performance claim.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('connections',len(rows),'changed paths',changed,'budget violations',violations,'pin counters',m,f)
