"""Full development sequence from empty state, graph/floors construction paid."""
import json,sys,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from tree_floor_predictor_seed_v3 import grouped_floor
from mcnc_bounded_owner_sequence_v1 import sequence
from source_binding_v2 import closure
base=R/'experiments/mcnc_prospective_v1_2026-10-07';out=R/'experiments/mcnc_bounded_owner_sequence_v1_2026-10-07';out.mkdir();inputs={};sources=closure([Path(__file__)])
for name in ('bigkey','dsip','misex3'):
 ep=base/name/'endpoints.json';inputs[str(ep)]=sha(ep);inputs.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()})
protocol=dict(inputs=inputs,sources=sources,cases=['bigkey','dsip','misex3'],policy=dict(start='empty',order='NET/CID',max_batches=8,max_owner_nets_per_batch=4,search_deadline_seconds_per_design=120,budget='max1ns,ceil1.5*inputfloor',release='all other owners blocking unrestricted input minimum witness',reinsert='failed first then all released connections NET/CID',failed_batch='retain exact before records/ledger and stop'),scope='Post-outcome development full-cohort attempt. All construction, floors, witness/owner conversions, seed reconstruction, batches and continuation paid. No prepared candidate or native label input, no tuning/exclusion by outcome; no native integration/heldout/physical hardware claim.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for name in protocol['cases']:
 begin=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(base/name/'endpoints.json');construction=time.perf_counter()-begin;groups=defaultdict(set)
 for q in queries:groups[q['source']].add(q['sink'])
 start=time.perf_counter();floors={}
 for source,sinks in groups.items():floors.update({(source,sink):value for sink,value in grouped_floor(f,rc,source,sinks).items()})
 floor_seconds=time.perf_counter()-start;work=out/name;work.mkdir();(work/'floors.json').write_text(json.dumps([dict(source=u,sink=v,minimum_integer=d) for (u,v),d in sorted(floors.items())])+'\n');start=time.perf_counter()
 def observe(event):
  (work/f'batch{event["index"]}.json').write_text(json.dumps(event)+'\n');print(name,'batch',event['index'],event['committed'],event['batch_failure'],flush=True)
 state,events,stop=sequence(f,rc,queries,floors,deadline=start+120,observer=observe);state.update(graph_sha256=digest,scale=rc.scale);(work/'candidate.json').write_text(json.dumps(state)+'\n');rows.append(dict(name=name,construction_seconds=construction,floor_seconds=floor_seconds,sequence_seconds=time.perf_counter()-start,total_seconds=time.perf_counter()-begin,stop=stop,completed=state['completed_connections'],required=state['required_connections'],batches=len(events),commits=sum(e['committed'] for e in events),files={str(p):sha(p) for p in work.iterdir() if p.is_file()}));(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,stop,state['completed_connections'],len(queries),flush=True)
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
