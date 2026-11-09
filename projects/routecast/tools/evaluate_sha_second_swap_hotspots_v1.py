"""Frozen cold labels, full positive CHAN universe; no fitted parameters."""
import json, sys, time, xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter, defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare
from audit_native_route import NET, NODE

name=sys.argv[1];out=R/'experiments/sha_second_swap_hotspots_v1_2026-10-10'/name
assert not out.exists(), "new evidence directory required"
out.mkdir(parents=True)
bindings=closure([Path(__file__)])
def load(path):
    bindings[str(path)]=sha(path)
    return json.loads(path.read_text())
def proof(path,flag):
    d=load(path)
    assert d[flag] and all(sha(k)==v for k,v in d['bindings'].items())
    bindings.update(d['bindings'])
    return d
tick=time.perf_counter()
protocol=load(R/'experiments/sha1_frozen_model_v1_2026-10-10/protocol.json')
assert all(sha(k)==v for k,v in protocol['bindings'].items())
bindings.update(protocol['bindings'])
assert name=='sha1' and protocol['required']==6273 and protocol['metrics']['spatial_k']==20
addendum=load(R/'experiments/sha1_frozen_model_v1_2026-10-10/metric_rule_addendum.json')
candidate=R/'experiments/sha1_frozen_model_v1_2026-10-10'
proof(candidate/'verification.json','complete_candidate_physical_and_events_pass')
resident=R/'experiments/sha_second_swap_complete_workflow_v1_2026-10-10/seed/model/sha1';proof(R/'experiments/sha_second_swap_complete_workflow_v1_2026-10-10/verification.json','all_cases_both_complete_arms_authenticated')
proof(resident/'verification.json','complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass')
proof(resident/'verification.json','complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass')
for frame in ['initial','sketch']:
    proof(resident/(frame+'_physical_verification.json'),'all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass')
c=load(resident/'sketch.json'); initial=load(resident/'initial.json')
ep=load(R/'experiments/sha_second_swap_complete_workflow_v1_2026-10-10/cold/demand/sha1/endpoints.json')
proof(R/'experiments/sha_second_swap_complete_workflow_v1_2026-10-10/cold/demand/sha1/verification.json','exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass')
assert all(x['completed_connections']==x['required_connections']==len(ep['connections']) for x in [c,initial])
cold=R/'experiments/sha_second_swap_complete_workflow_v1_2026-10-10/cold/native/sha1'
proof(cold/'verification.json','all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass')
canonical=load(R/'experiments/sha_second_swap_complete_workflow_v1_2026-10-10/cold/canonical/receipt.json')['rows'][0]['canonical']
assert canonical['semantic_consistency_gate_pass']
ignored=load(R/'experiments/sha_second_swap_complete_workflow_v1_2026-10-10/cold/canonical/ignored_pin_verification_v1.json')
assert all(sha(k)==v for k,v in ignored['bindings'].items())
bindings.update(ignored['bindings'])
assert ignored['rows'][0]['every_mismatch_matches_native_ignored_sink_pin'] and ignored['rows'][0]['post_reload_packed_netlist_byte_identical']
native=load(cold/'physical_audit.json')
assert sha(R/'experiments/sha_second_swap_complete_workflow_v1_2026-10-10/cold/rr/sha1/rr_graph.xml')==ep['graph_sha256']
route=cold/'output.route';bindings[str(route)]=sha(route)
# Independent native per-NET union reconstruction, including repeated branch nodes.
used={}; net=None
for line in route.read_text().splitlines():
    if m:=NET.match(line):
        net=int(m[1]);assert net not in used;used[net]=set()
    elif m:=NODE.match(line):
        assert net is not None;used[net].add(int(m[1]))
truth=Counter(n for nodes in used.values() for n in nodes)
assert {int(n):v for n,v in native['node_occupancy'].items() if v}==dict(truth)
geo_dir=R/'experiments/sha_second_swap_geometry_v1_2026-10-10'/name
receipt=load(geo_dir/'receipt.json')
assert receipt['native_labels_used'] is False and all(sha(k)==v for k,v in receipt['bindings'].items())
bindings.update(receipt['bindings'])
geo_file=geo_dir/'prediction.json';assert sha(geo_file)==receipt['prediction_sha256']
geo=load(geo_file); geo_bins={tuple(x['key']):x for x in geo['bins']}
assert len(geo_bins)==len(geo['bins']) and geo['required_queries']==len(ep['connections'])
round0=load(resident/'round0.json')
ledgers={'final_shared':c['ledger'],'final_independent':c['independent_connection_ledger'],'rc_initial':initial['ledger'],'round0_shared':round0['ledger']}
graph=Path(ep['inputs']['graph']['path']);bindings[str(graph)]=sha(graph);assert sha(graph)==ep['graph_sha256']
channels=[];caps=Counter();td=Counter();pd={m:Counter() for m in ledgers};stack=[]
for event,el in E.iterparse(graph,events=('start','end')):
    if event=='start':stack.append(el);continue
    if el.tag=='node' and el.get('type') in {'CHANX','CHANY'} and int(el.get('capacity'))>0:
        n=int(el.get('id'));cap=int(el.get('capacity'));loc=el.find('loc').attrib;seg=el.find('segment');segment=int(seg.get('segment_id')) if seg is not None else -1
        values={m:l.get(str(n),0) for m,l in ledgers.items()}
        channels.append(dict(node=n,capacity=cap,native=truth.get(n,0),predictions=values))
        for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
            for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
                k=(int(loc.get('layer','0')),x,y,el.get('type'),segment)
                caps[k]+=cap;td[k]+=truth.get(n,0)
                for m in ledgers:pd[m][k]+=values[m]
    if el.tag in {'node','edge'}:
        if len(stack)>1:stack[-2].remove(el)
        el.clear()
    stack.pop()
channels.sort(key=lambda x:x['node'])
assert set(caps)==set(geo_bins) and all(caps[k]==geo_bins[k]['capacity'] for k in caps)
bins=[dict(key=list(k),capacity=caps[k],native=td[k],geometry=geo_bins[k]['geometry'],predictions={m:pd[m][k] for m in ledgers}) for k in sorted(caps)]
metrics={m:{'concrete':compare({x['node']:x['predictions'][m]/x['capacity'] for x in channels},{x['node']:x['native']/x['capacity'] for x in channels},max(1,len(channels)//20)), 'spatial':compare({tuple(x['key']):x['predictions'][m]/x['capacity'] for x in bins},{tuple(x['key']):x['native']/x['capacity'] for x in bins},20)} for m in ledgers}
metrics['geometry']={'concrete':None,'spatial':compare({tuple(x['key']):x['geometry'] for x in bins},{tuple(x['key']):x['native']/x['capacity'] for x in bins},20)}
vf=out/'comparison_vectors.json';vf.write_text(json.dumps(dict(channels=channels,bins=bins))+'\n');bindings[str(vf)]=sha(vf)
assert all(sha(k)==v for k,v in bindings.items())
(out/'comparison.json').write_text(json.dumps(dict(bindings=bindings,required=len(ep['connections']),completed=len(ep['connections']),metrics=metrics,overflow_units={m:sum(max(0,x['predictions'][m]-x['capacity']) for x in channels) for m in ledgers},heldout_family=False,evaluation_seconds=time.perf_counter()-tick,native_label_case='frozen cold only',scope='SHA compatibility evaluation with model and metric parameters frozen before cold labels. Source-family/global independence unresolved; not strict heldout validation. Original zero-counter canonical gate remains false; separate semantic reload passes. Geometry has no concrete resource prediction. Descriptive prediction metrics, not timing or net-gain proof.'),indent=2)+'\n')
print('METRICS',json.dumps(metrics),flush=True)
