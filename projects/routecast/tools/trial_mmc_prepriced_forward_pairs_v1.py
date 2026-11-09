"""Full archived multi-sink schedule, alternating paired original/candidate calls."""
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from soft_demand_workspace_bridge_v1 import Search as Control
from soft_demand_workspace_prepriced_v2 import Search as Candidate
from freeze_requested_search_result_v1 import freeze_requested

R = Path(__file__).resolve().parents[1]
D = R/'experiments/ultraembedded_mmc_actual_old_linear_expat_workflow_v15_2026-10-10'
P = R/'experiments/mmc_prepriced_model_v1_2026-10-10/verification.json'
O = R/'experiments/mmc_prepriced_forward_pairs_v1_2026-10-10'
proof = json.loads(P.read_text())
assert proof['complete_candidate_physical_and_events_pass'] and proof['complete_states_and_events_equal_control']
bindings = closure([Path(__file__)])
for p,h in proof['bindings'].items():
    assert sha(p)==h
    bindings[p]=h
bindings[str(P)]=sha(P)
ep = D/'seed/demand/mmc/endpoints.json'
for p in [ep,D/'seed/model/mmc/receipt.json',D/'seed/model/mmc/round0.json',D/'seed/model/mmc/round1.json']:
    bindings[str(p)]=sha(p)
old = R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so'
new = R/'experiments/soft_demand_workspace_prepriced_build_v5_2026-10-10/search.so'
for p in [old,new]: bindings[str(p)]=sha(p)
O.mkdir()
(O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,
    policy='All archived multi-unique-sink NET requests in each of three phases; alternating control-first/candidate-first per NET. Two owned workspaces, unchanged requested-path interface. Preparation measured separately. No randomization or fresh feedback ledger generation.'),indent=2)+'\n')
graph,digest,nodes,f,rc,queries = load_endpoints(ep)
groups=defaultdict(list)
for q in queries: groups[q['net_id']].append(q)
receipt=json.loads((D/'seed/model/mmc/receipt.json').read_text())
phases=[(sorted(groups),{},0)]
for i,round_ in enumerate(receipt['rounds']):
    state=json.loads((D/f'seed/model/mmc/round{i}.json').read_text())
    phases.append((round_['affected_nets'],{int(k):v for k,v in state['prices'].items()},rc.scale//(20*10**9)))
engines={'control':Control(f,rc,old),'candidate':Candidate(f,rc,new)}
rows=[]
for phase,(nets,prices,weight) in enumerate(phases):
    selected=[n for n in nets if len({q['sink'] for q in groups[n]})>1]
    assert len(selected)==[6666,6666,6205][phase]
    preparation={}
    for name in (['control','candidate'] if phase%2==0 else ['candidate','control']):
        tick=time.perf_counter();engines[name].prepare(prices,weight)
        preparation[name]=time.perf_counter()-tick
    totals=defaultdict(float);counts=defaultdict(int)
    for i,net in enumerate(selected):
        qs=groups[net];source=qs[0]['source'];assert all(q['source']==source for q in qs)
        targets={q['sink'] for q in qs};order=['control','candidate'] if i%2==0 else ['candidate','control']
        results={}
        for name in order:
            tick=time.perf_counter();raw,parents,settled=engines[name].search(source,targets)
            totals[name]+=time.perf_counter()-tick
            results[name]=freeze_requested(source,targets,raw,parents,settled)
        assert results['control']==results['candidate'],(phase,net)
        counts[order[0]+'_first']+=1
    rows.append(dict(phase=phase,nets=len(selected),requested_sinks=sum(len({q['sink'] for q in groups[n]}) for n in selected),
                     search_seconds=dict(totals),prepare_seconds=preparation,order_counts=dict(counts),all_requested_paths_equal=True))
    (O/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows[-1],flush=True)
for engine in engines.values():engine.close()
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,complete_three_phase_multi_sink_requested_paths_equal=True,rows=rows,
         additional_owned_price_bytes=16*len(f['capacities']),
         scope='Full archived multi-sink schedule diagnostic only. Freeze/comparison excluded from search timers; prepare explicitly included separately. Alternating pair order, not randomized stable/fresh model/full workflow or heldout/silicon gain.')
(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print('COMPLETE full paired multi-sink search diagnostic',flush=True)
