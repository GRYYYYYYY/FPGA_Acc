"""Complete explicit-pin native-path additive proxy budget compatibility, evaluator only."""
import datetime
import gc
import json
import resource
import sys
import time
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from native_tagged_route_walk_v2 import walk
from independent_fraction_arc_context_v2 import load_context,arc_delay
from exact_rc_lattice_direct_pairs_v2 import exact_scale
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha

OUT=R/'experiments/neuron_native_proxy_budget_compatibility_v2_2026-10-17'


def load(p):return json.loads(Path(p).read_text())
def stamp(p):
    s=Path(p).stat();return s.st_ino,s.st_size,s.st_mtime_ns


def main():
    start=time.perf_counter();free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
    assert free>=36*2**30 # reserve full20GiB live model, own8GiB, shared8GiB margin
    resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
    endpoint=R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'
    route=R/'experiments/titan23_neuron_native_cold_label_v1_2026-10-14/output.route'
    native_audit=R/'experiments/titan23_neuron_native_label_audit_v2_2026-10-15/physical_audit.json'
    label=R/'experiments/neuron_certified_native_metrics_v1_2026-10-15/label_admission.json'
    initial=R/'experiments/neuron_quotient_astar_pipeline_v1_2026-10-17/model/initial.json'
    admission=initial.parent.parent/'independent_final_admission_v1.json'
    crit=R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality/initial_connection_criticalities.json'
    cp=crit.parent/'verification.json';ep=load(endpoint);graph=Path(ep['inputs']['graph']['path'])
    certified=load(label);assert certified['label_accepted'];assert load(admission)['all_pass']
    cv=load(cp);assert cv['nonignored_pin_keys_exactly_manifest'] and cv['bindings'][str(crit)]==sha(crit)
    inputs=[endpoint,route,native_audit,label,initial,admission,crit,cp,graph]
    bindings=closure([Path(__file__),R/'tools/verify_native_tagged_route_walk_v2.py'])
    for p in inputs:
        bindings[str(p)]=sha(p)
        if str(p) in certified['bindings']:assert bindings[str(p)]==certified['bindings'][str(p)]
    assert bindings[str(graph)]==ep['graph_sha256']
    before={str(p):stamp(p) for p in inputs}
    old=load(initial);assert old['completed_connections']==old['required_connections']==77106
    budgets={x['connection_id']:(x['net_id'],x['source'],x['sink'],x['floor_integer'],x['budget_integer']) for x in old['records']};del old;gc.collect()
    queries={q['connection_id']:q for q in ep['connections']};assert set(budgets)==set(queries)==set(range(77106))
    expected={};fanouts=Counter(q['net_id'] for q in queries.values())
    for row in load(crit):
        cid=row['connection_id'];q=queries[cid];key=(row['net'],row['local_sink_pin'])
        assert key not in expected and (row['net'],row['source_rr'],row['target_rr'])==(q['net_id'],q['source'],q['sink'])==budgets[cid][:3]
        expected[key]=cid
    assert len(expected)==77106 and len(fanouts)==50767
    physical=load(native_audit);assert physical['inputs_sha256']['route']==bindings[str(route)]
    assert Counter((x['net_id'],x['source'],x['sink']) for x in physical['connections'])==Counter(v[:3] for v in budgets.values())
    truth=physical['node_occupancy'];certified_hops=Counter((x['net_id'],x['source'],x['sink'],x['hops']) for x in physical['connections']);del physical;gc.collect()
    OUT.mkdir()
    (OUT/'protocol.json').write_text(json.dumps(dict(bindings=bindings,created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        original_connections=77106,required_NETs=50767,join='Explicit native NET/local Net_pin_index to frozen perpin CID; SOURCE/SINK identity and complete occurrence multiset independently checked. No singleton exclusion.',
        scope='Evaluator-only already-exposed native reference. Same exact additive proxy cost on physical native paths vs original frozen floor/budget. Not native Elmore/STA, actual native timing constraint failure, prediction, new label or budget tuning.',
        resource_limit_bytes=8*2**30,shared_headroom_bytes=free,reserved_other_model_and_margin_bytes=28*2**30,promoted=False),indent=2)+'\n')
    needed=set()
    for event in walk(route):
        if event[0]=='arc':needed.add(event[2:])
    xml,ids,classes,switches,digest=load_context(graph,ep['graph_sha256']);assert digest==ep['graph_sha256']
    scale,pair_count=exact_scale(ids,classes,switches,xml.graph.edges)
    found_arcs=set();edge_count=0
    for u,v,sw in zip(xml.graph.edges.source,xml.graph.edges.destination,xml.graph.edges.switch):
        edge_count+=1
        if (u,v,sw) in needed:found_arcs.add((u,v,sw))
    assert edge_count==39165143 and found_arcs==needed
    del needed,found_arcs;gc.collect()
    seen=set();nodes=Counter();prefix={};hops={};used=set();net=None;total=Counter();by_net=defaultdict(Counter);measured_hops=Counter();maximum_ratio=Fraction(0)
    with (OUT/'reference_rows.jsonl').open('x') as output:
        for event in walk(route):
            kind=event[0]
            if kind=='net':
                if net is not None:nodes.update(used)
                net=event[1];prefix={};hops={};used=set()
                if net in fanouts:assert event[2]==ep['net_names'][str(net)]
            elif kind=='source':
                nid=event[2];assert xml.graph.nodes[nid].type=='SOURCE' and xml.graph.nodes[nid].capacity>0
                a,b=classes[ids[nid]];prefix[nid]=a*b/2;hops[nid]=0;used.add(nid)
            elif kind=='arc':
                _,_,u,v,sw=event;assert u in prefix and xml.graph.nodes[v].capacity>0
                prefix[v]=prefix[u]+arc_delay(classes,switches,ids[v],sw);hops[v]=hops[u]+1;used.add(v)
            elif kind=='sink':
                _,_,source,sink,pin=event
                if net not in fanouts:continue
                key=(net,pin);assert key in expected;cid=expected[key];assert cid not in seen;seen.add(cid)
                assert budgets[cid][:3]==(net,source,sink) and xml.graph.nodes[sink].type=='SINK'
                value=prefix[sink]*scale;assert value.denominator==1;raw=value.numerator;floor,budget=budgets[cid][3:]
                assert raw>=floor>=0 and budget>=floor and budget>0
                feasible=raw<=budget;ratio=Fraction(raw,budget);maximum_ratio=max(maximum_ratio,ratio)
                total['connections']+=1;total['proxy_budget_violations']+=not feasible
                by_net[net]['connections']+=1;by_net[net]['proxy_budget_violations']+=not feasible
                measured_hops[(net,source,sink,hops[sink])]+=1
                output.write(json.dumps(dict(connection_id=cid,net_id=net,local_sink_pin=pin,source=source,sink=sink,hops=hops[sink],native_path_additive_integer=raw,floor_integer=floor,budget_integer=budget,proxy_budget_feasible=feasible))+'\n')
    nodes.update(used)
    assert seen==set(queries) and len(seen)==77106 and measured_hops==certified_hops
    assert {str(n):v for n,v in nodes.items()}==truth
    assert sum(x['connections'] for x in by_net.values())==77106 and len(by_net)==50767
    assert all(stamp(p)==s for p,s in before.items()) and all(sha(p)==h for p,h in bindings.items())
    bindings[str(OUT/'reference_rows.jsonl')]=sha(OUT/'reference_rows.jsonl')
    result=dict(all_pass=True,bindings=bindings,all_original_CIDs_with_explicit_pin_identity=True,all_native_hops_and_unique_NET_node_occupancy_match_certified=True,
        all_native_arcs_match_original_graph=True,graph_edges_checked=edge_count,electrical_pair_count=pair_count,scale=scale,
        summary=dict(total),NETs=50767,per_NET={str(n):dict(v) for n,v in sorted(by_net.items())},
        maximum_exact_native_proxy_to_budget_ratio=str(maximum_ratio),seconds=time.perf_counter()-start,peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        scope='Complete already-exposed reference compatibility diagnostic. Additive proxy budgets are not native STA/Elmore constraints. No candidate/model changes, no budget retuning, no new labels, no strict-unseen or workflow gain.',promoted=False)
    (OUT/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('bindings','per_NET')},indent=2),flush=True)


if __name__=='__main__':main()
