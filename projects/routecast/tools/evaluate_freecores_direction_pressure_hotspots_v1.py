"""Previously observed fixed cold labels, full positive CHAN universe, direction-pressure development control; no fitted parameters."""
import json, sys, time, xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter, defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare
from audit_native_route import NET, NODE

name=sys.argv[1];mode=sys.argv[2];assert mode in ('within_polarity','across_polarity');out=R/'experiments/freecores_direction_pressure_hotspots_v1_2026-10-08'/name/mode
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
protocol=load(R/'experiments/freecores_prospective_evaluation_prereg_v1_2026-10-08/protocol.json')
assert all(sha(k)==v for k,v in protocol['bindings'].items())
bindings.update(protocol['bindings'])
assert name in protocol['cases'] and protocol['metrics']['spatial_top_k']==20 and protocol['metrics']['label_case']=='Fixed cold route only, not best seed/case/round choice'
resident=R/'experiments/freecores_direction_pressure_model_v2_2026-10-08'/name/mode/'resident'
event_proof=proof(resident/'verification.json','complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass')
assert event_proof['pressure_mode']==mode and event_proof['actual_projected_price_changes_and_independent_groupmeans_pass']
for frame in ['initial','sketch']:
    proof(resident/(frame+'_physical_verification.json'),'all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass')
c=load(resident/'sketch.json'); initial=load(resident/'initial.json')
ep=load(R/'experiments/freecores_native_demand_v1_2026-10-08'/name/'endpoints.json')
assert all(x['completed_connections']==x['required_connections']==len(ep['connections']) for x in [c,initial])
cold=R/'experiments/freecores_native_cold_v1_2026-10-08'/name
proof(cold/'verification.json','all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass')
proof(R/'experiments/freecores_cold_canonical_v1_2026-10-08/admission_review.json','both_cold_canonical_consistency_and_ignored_pin_identity_pass')
native=load(cold/'physical_audit.json')
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
geo_dir=R/'experiments/freecores_geometry_v1_2026-10-08'/name
receipt=load(geo_dir/'receipt.json')
assert receipt['native_labels_used'] is False and all(sha(k)==v for k,v in receipt['bindings'].items())
bindings.update(receipt['bindings'])
geo_file=geo_dir/'prediction.json';assert sha(geo_file)==receipt['prediction_sha256']
geo=load(geo_file); geo_bins={tuple(x['key']):x for x in geo['bins']}
assert len(geo_bins)==len(geo['bins']) and geo['required_queries']==len(ep['connections'])
ledgers={'wire_shared':c['ledger'],'wire_independent':c['independent_connection_ledger'],'rc_initial':initial['ledger']}
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
(out/'comparison.json').write_text(json.dumps(dict(bindings=bindings,required=len(ep['connections']),completed=len(ep['connections']),metrics=metrics,evaluation_seconds=time.perf_counter()-tick,native_label_case='frozen cold only',scope='Known-label within/across polarity pressure development control; same full frozen cold universe, original topology and RC. No strict heldout/prospective or topology-direction erasure claim. Geometry has no concrete resource prediction. Descriptive prediction metrics, not timing or net-gain proof.'),indent=2)+'\n')
print('METRICS',json.dumps(metrics),flush=True)
