"""Independent node-wise occupancy subtraction and retained tree invariants."""
import json,shlex,sys
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_work_metrics import extract
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'experiments/native_resume_state_trace_v6_2026-10-07'
rp=base/'receipt.json';r=json.loads(rp.read_text());rows=[]
for x in r['rows']:
 work=base/x['mode'];log=work/'run.log';assert sha(log)==x['log_sha256'] and x['exit_code']==0 and x['full_check']
 if x['mode']=='cold':continue
 trace=work/'state.trace';stages={stage:dict(occ={},trees=defaultdict(Counter),delays={}) for stage in ('before','after')}
 for line in trace.read_text().splitlines():
  q=shlex.split(line);d=stages[q[1]]
  if q[0]=='O':assert int(q[2]) not in d['occ'];d['occ'][int(q[2])]=int(q[3])
  elif q[0]=='T':d['trees'][q[3]][int(q[4]),int(q[5])]+=1
  elif q[0]=='D':key=(int(q[2]),int(q[3]));assert key not in d['delays'];d['delays'][key]=q[4]
  else:raise AssertionError('unknown trace row')
 a,b=stages['before'],stages['after'];assert a['occ'].keys()==b['occ'].keys() and a['delays']==b['delays']
 removed={'d2_0'} if x['mode']=='resume_remove' else set()
 assert a['trees'].keys()-b['trees'].keys()==removed and not b['trees'].keys()-a['trees'].keys()
 for name in b['trees']:assert a['trees'][name]==b['trees'][name]
 delta=Counter()
 for name in removed:
  for (node,pin),count in a['trees'][name].items():delta[node]+=count
 assert all(b['occ'][n]==a['occ'][n]-delta[n] and b['occ'][n]>=0 for n in a['occ'])
 # Exposed tree union IDs also match the actual seed route, including all NETs.
 seed=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/design.route'
 paths=physical_paths(seed);expected={name:{n for path in ps for n,_ in path} for name,ps in paths.items() if ps}
 assert {name:{n for n,pin in values} for name,values in a['trees'].items()}==expected
 metrics=extract(log.read_text());rows.append(dict(mode=x['mode'],nodes_checked=len(a['occ']),loaded_trees=len(a['trees']),remaining_trees=len(b['trees']),removed_tree_nodes=sum(delta.values()),all_node_occupancy_delta_exact=True,retained_tree_node_pin_multisets_unchanged=True,all_initial_delay_entries_unchanged=True,seed_tree_union_ids_match=True,trace_sha256=sha(trace),native_iterations=metrics['iterations'],connection_attempts=metrics['rerouted_connection_attempts']))
# Instrumentation preserves v4 final paths.
norm=lambda f:{n:Counter(ps) for n,ps in physical_paths(f).items() if ps}
for x in r['rows']:assert norm(base/x['mode']/'output.route')==norm(ROOT/'experiments/native_resume_remove_v4_2026-10-07'/x['mode']/'output.route')
(base/'state_verification.json').write_text(json.dumps(dict(receipt_sha256=sha(rp),verifier_sha256=sha(Path(__file__)),rows=rows,instrumented_final_paths_equal_v4=True,scope='All RR occupancy delta and retained node/pin trees checked before first iteration; no edge/timing-field/internal CBRR trace. Previous achieved delays unchanged as estimates for removed NET, not certified incomplete-state STA. Same placement only; no netgain.'),indent=2)+'\n');print(rows)
