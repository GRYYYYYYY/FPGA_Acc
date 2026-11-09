"""Original XML/Fraction witness for a budget-filtered retained forest, not native import."""
import json
import sys
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
from stream_native_route_audit_cached import audit
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read
from fraction_arc_cache_v1 import FractionArcCache
P=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
prior=R/'experiments/endpoint_changed_branch_scope_v1_2026-10-08/diagnosis.json'
certificate=json.loads(prior.read_text());assert all(sha(p)==h for p,h in certificate['bindings'].items())
bindings={**certificate['bindings'],**closure([Path(__file__)]),str(prior):sha(prior)}
D=R/'experiments/endpoint_compatible_branch_trim_v1_2026-10-08';D.mkdir(exist_ok=False)
rows=[];contexts={}
for case in json.loads(P.read_text())['cases']:
    old,target=[json.loads(Path(case[k]).read_text()) for k in ['old','target']]
    graph=Path(old['inputs']['graph']['path']);route=graph.with_name('design.route')
    bindings[str(route)]=sha(route);budget_path=Path(case['budget']);bindings[str(budget_path)]=sha(budget_path)
    assert route.read_text().splitlines()[0].endswith('SHA256:'+old['inputs']['place']['sha256'])
    if case['width'] not in contexts:
        physical=audit(graph,route);assert physical['all_printed_branch_arc_switch_and_union_checks_pass'] and physical['overflow_units']==0
        xml=ImmutableXMLAudit(graph,old['graph_sha256']);ids,classes,switches,digest=read(graph)
        assert digest==old['graph_sha256'];cost=FractionArcCache(classes,switches)
        arcs=defaultdict(list)
        for eid in range(len(xml.graph.edges)):
            e=xml.graph.edges[eid];arcs[e.source,e.sink,e.switch_id].append(eid)
        contexts[case['width']]=(xml,ids,classes,cost,arcs,physical_paths(route))
    xml,ids,classes,cost,arcs,paths=contexts[case['width']]
    assert xml.digest==target['graph_sha256']==old['graph_sha256']
    original={q['connection_id']:q for q in old['connections']};queries={q['connection_id']:q for q in target['connections']}
    grouped=defaultdict(list)
    for q in original.values():grouped[(old['net_names'][str(q['net_id'])],q['source'],q['sink'])].append(q)
    observed=defaultdict(list)
    for name,branches in paths.items():
        for branch in branches:observed[name,branch[0][0],branch[-1][0]].append(branch)
    assert grouped.keys()==observed.keys()
    assigned={}
    for key,qs in grouped.items():
        branches=observed[key];assert len(branches)==len(qs)
        assert len(set(branches))==1,'Ambiguous repeated terminal identity requires packed-pin mapping'
        for q in qs:assigned[q['connection_id']]=branches[0]
    budget=json.loads(budget_path.read_text());parents=defaultdict(dict);owned=defaultdict(set);retained=[];released=[]
    dirty={q['net_id'] for cid,q in queries.items() if (q['source'],q['sink'])!=(original[cid]['source'],original[cid]['sink'])}
    compatible_in_dirty=budget_rejected=0
    for cid,q in sorted(queries.items()):
        before=original[cid]
        if (q['source'],q['sink'])!=(before['source'],before['sink']):
            released.append(dict(connection_id=cid,reason='ENDPOINT_CHANGED'));continue
        branch=assigned[cid];u=q['source'];seen={u};edges=[];incoming={};a,b=classes[ids[u]];delay=a*b/2
        assert xml.graph.nodes[u].capacity>0 and branch[0]==(u,None)
        for v,switch in branch[1:]:
            assert v not in seen and xml.graph.nodes[v].capacity>0
            candidates=arcs[u,v,switch];assert len(candidates)==1
            eid=candidates[0];edges.append(eid);incoming[v]=(u,eid);delay+=cost(ids[v],switch);seen.add(v);u=v
        assert u==q['sink']
        limit=Fraction(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))
        if delay*10**9>limit:
            budget_rejected+=1;released.append(dict(connection_id=cid,reason='TARGET_BUDGET_UNSAFE',delay_seconds=str(delay),budget_ns=str(limit)));continue
        net=q['net_id']
        for node,parent in incoming.items():assert node not in parents[net] or parents[net][node]==parent
        parents[net].update(incoming);owned[net].update(seen)
        compatible_in_dirty+=net in dirty
        retained.append(dict(q,physical_edge_ids=edges,delay_seconds=str(delay),budget_ns=str(limit)))
    ledger=Counter(n for used in owned.values() for n in used)
    assert all(0<c<=xml.graph.nodes[n].capacity for n,c in ledger.items())
    assert len(retained)+len(released)==len(queries)
    assert {q['connection_id'] for q in retained}|{q['connection_id'] for q in released}==queries.keys()
    file=D/f"w{case['width']}_m{case['index']}.json"
    file.write_text(json.dumps(dict(retained=retained,released=released,ledger=dict(ledger),parents={str(n):{str(v):p for v,p in ps.items()} for n,ps in parents.items()}))+'\n')
    rows.append(dict(width=case['width'],index=case['index'],required=len(queries),retained=len(retained),released=len(released),target_budget_rejected=budget_rejected,retained_inside_endpoint_changed_NETs=compatible_in_dirty,file=str(file),sha256=sha(file)))
    print(json.dumps(rows[-1]),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,
    scope='Budget-filtered endpoint-compatible forest with original physical arc/Fraction RC/single-parent/unique-NET capacity witnesses. Missing branches explicitly released, not routed. No changed-price optimality, native incomplete-NET import, full STA, heldout or runtime gain proof.'),indent=2)+'\n')
