"""Five alternating complete primitive pairs, including both workspace setups."""
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from time import perf_counter
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from soft_demand_workspace_bridge_v1 import Search
from bidirectional_rc_bridge_v1 import Bidirectional

name=sys.argv[1];assert name in ['xtea','mmc','8051']
original=R/'experiments/real_rr_bidirectional_single_sink_v2_2026-10-08'/name
proof_path=original/'verification.json'
proof=json.loads(proof_path.read_text())
assert proof['complete_single_target_primitive_pass']
assert all(sha(p)==h for p,h in proof['bindings'].items())
receipt=json.loads((original/'receipt.json').read_text())
bindings={**proof['bindings'],**closure([Path(__file__)]),str(proof_path):sha(proof_path)}
ep=next(Path(p) for p in bindings if p.endswith('/endpoints.json'))
forward_binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
candidate_binary=R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so'
graph,digest,nodes,f,rc,queries=load_endpoints(ep)
groups=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
selected=sorted((n,qs[0]) for n,qs in groups.items() if len({q['sink'] for q in qs})==1)
contexts=[]
for phase in ['initial','round0','round1']:
    prices={} if phase=='initial' else {int(k):v for k,v in json.loads(next(Path(p) for p in receipt['bindings'] if p.endswith('/'+phase+'.json')).read_text())['prices'].items()}
    expected=json.loads((original/(phase+'.json')).read_text())
    contexts.append((phase,prices,0 if phase=='initial' else rc.scale//(20*10**9),expected))
D=R/'experiments/paired_bidirectional_primitive_v2_2026-10-08'/name
D.mkdir(parents=True,exist_ok=False)
protocol=dict(bindings=bindings,pairs=5,order=[['baseline','candidate'] if i%2==0 else ['candidate','baseline'] for i in range(5)],
    complete_nets=len(selected),phases=['initial','round0','round1'],
    scope='Fresh workspace setup, all three prepare costs, complete queries and common path audit inside each arm. Common original graph parse and frozen expected-data load excluded. Not full mixed model or end-to-end workflow.')
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
def run(mode):
    tick=perf_counter()
    search=Search(f,rc,forward_binary) if mode=='baseline' else Bidirectional(f,rc,candidate_binary)
    setup=perf_counter()-tick;rows=[]
    for phase,prices,weight,expected in contexts:
        start=perf_counter();search.prepare(prices,weight)
        for n,q in selected:
            source,sink=q['source'],q['sink']
            if mode=='baseline':
                raw,parents,settled=search.search(source,{sink});assert sink in settled
                u=sink;slots=[]
                while u!=source:u,e=parents[u];slots.append(e)
                slots.reverse();delay=raw[sink]
                objective=delay+weight*sum(prices.get(f['dest_ranks'][e],0) for e in slots)
            else:
                answer=search.search(source,sink);assert answer is not None
                slots,delay,objective=answer['slots'],answer['raw'],answer['objective']
            u=source;seen={u};raw_check=rc.initial(source);cost=raw_check
            for e in slots:
                assert f['row_offsets'][u]<=e<f['row_offsets'][u+1]
                u=f['dest_ranks'][e];assert f['capacities'][u] and u not in seen;seen.add(u)
                raw_check+=rc.increments[e];cost+=rc.increments[e]+weight*prices.get(u,0)
            assert u==sink and raw_check==delay and cost==objective
            actual=dict(source=source,sink=sink,physical_edge_ids=[f['edge_ids'][e] for e in slots],delay=delay,objective=objective)
            assert actual==expected[mode][str(n)]
        rows.append(dict(phase=phase,seconds=perf_counter()-start,complete_nets=len(selected)))
    search.close()
    return dict(setup_seconds=setup,phases=rows,total_seconds=perf_counter()-tick,all_frozen_paths_exact=True)
pairs=[]
for i,order in enumerate(protocol['order']):
    arms={mode:run(mode) for mode in order}
    result=dict(pair=i,order=order,arms=arms,ratio=arms['candidate']['total_seconds']/arms['baseline']['total_seconds'])
    pairs.append(result)
    (D/f'pair{i}.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(pair=i,ratio=result['ratio'])),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,pairs=pairs,median_ratio=statistics.median(x['ratio'] for x in pairs),
    candidate_faster_pairs=sum(x['ratio']<1 for x in pairs),scope=protocol['scope'],
    files={str(p):sha(p) for p in D.iterdir() if p.is_file()})
(D/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(median_ratio=result['median_ratio'],candidate_faster_pairs=result['candidate_faster_pairs'])))
