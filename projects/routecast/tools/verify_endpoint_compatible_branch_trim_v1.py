"""Independent native backpointer parser and direct XML electrical/tree audit."""
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path
from audit_native_route import NET,NODE
from path_rc import number
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
D=R/'experiments/endpoint_compatible_branch_trim_v1_2026-10-08'
r=json.loads((D/'receipt.json').read_text())
bindings={**r['bindings'],**closure([Path(__file__)]),str(D/'receipt.json'):sha(D/'receipt.json')}
assert all(sha(p)==h for p,h in bindings.items())
protocol=json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())
contexts={};results=[]
for case,row in zip(protocol['cases'],r['rows']):
    assert (case['width'],case['index'])==(row['width'],row['index'])
    old,target=[json.loads(Path(case[k]).read_text()) for k in ['old','target']]
    graph=Path(old['inputs']['graph']['path']);route=graph.with_name('design.route')
    if case['width'] not in contexts:
        root=ET.parse(graph).getroot();nodes=list(root.find('rr_nodes'));edges=list(root.find('rr_edges'))
        rc=[(number(n.find('timing').get('R')),number(n.find('timing').get('C'))) for n in nodes]
        switches={int(s.get('id')):(number(s.find('timing').get('R','0')),number(s.find('timing').get('Tdel','0'))) for s in root.find('switches') if s.tag=='switch'}
        arcs=[(int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))) for e in edges]
        index=defaultdict(list)
        for eid,key in enumerate(arcs):index[key].append(eid)
        native=defaultdict(list);name=None;parents={};previous=None;outgoing=None
        for line in route.read_text().splitlines():
            m=NET.match(line)
            if m:name=m[2];parents={};previous=None;outgoing=None
            m=NODE.match(line)
            if not m:continue
            node,kind,sid=int(m[1]),m[2],int(m[3]);assert name is not None
            if kind=='SOURCE':assert not parents;parents[node]=None
            elif kind=='SINK':
                u=previous;path=[(previous,node,outgoing)];seen={node}
                while parents[u] is not None:
                    assert u not in seen;seen.add(u);p,s=parents[u];path.append((p,u,s));u=p
                path.reverse();native[name,u,node].append(path)
            elif node not in parents:
                assert previous in parents;parents[node]=(previous,outgoing)
            previous,outgoing=node,sid
        contexts[case['width']]=(nodes,rc,switches,arcs,index,native)
    nodes,rc,switches,arcs,index,native=contexts[case['width']]
    previous={q['connection_id']:q for q in old['connections']};queries={q['connection_id']:q for q in target['connections']}
    expected=Counter((old['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in previous.values())
    assert expected==Counter({k:len(v) for k,v in native.items()})
    file=Path(row['file']);assert sha(file)==row['sha256'];bindings[str(file)]=sha(file)
    data=json.loads(file.read_text());retained={q['connection_id']:q for q in data['retained']};released={q['connection_id']:q for q in data['released']}
    assert len(retained)==len(data['retained']) and len(released)==len(data['released'])
    assert not retained.keys()&released.keys() and retained.keys()|released.keys()==queries.keys()
    budgets=json.loads(Path(case['budget']).read_text());ownership=defaultdict(set);parents=defaultdict(dict);unsafe=0;dirty=set()
    for cid,q in queries.items():
        before=previous[cid]
        if (q['source'],q['sink'])!=(before['source'],before['sink']):
            dirty.add(q['net_id']);assert released[cid]['reason']=='ENDPOINT_CHANGED';continue
        key=(old['net_names'][str(q['net_id'])],q['source'],q['sink']);variants=native[key]
        assert all(p==variants[0] for p in variants)
        path=variants[0];a,b=rc[q['source']];delay=a*b/2
        for u,v,sid in path:
            sr,td=switches[sid];nr,nc=rc[v];delay+=(sr+nr/2)*nc+td
        limit=Fraction(budgets['budgets_ns'].get(str(cid),budgets['default_budget_ns']))
        if delay*10**9>limit:
            record=released[cid];assert record['reason']=='TARGET_BUDGET_UNSAFE'
            assert Fraction(record['delay_seconds'])==delay and Fraction(record['budget_ns'])==limit;unsafe+=1;continue
        record=retained[cid];assert all(record[k]==v for k,v in q.items())
        assert Fraction(record['delay_seconds'])==delay and Fraction(record['budget_ns'])==limit
        assert [arcs[e] for e in record['physical_edge_ids']]==path
        u=q['source'];used={u};assert nodes[u].get('type')=='SOURCE'
        for eid in record['physical_edge_ids']:
            p,v,sid=arcs[eid];assert p==u and v not in used and len(index[p,v,sid])==1
            parent=(p,eid);assert v not in parents[q['net_id']] or parents[q['net_id']][v]==parent
            parents[q['net_id']][v]=parent;used.add(v);u=v
        assert u==q['sink'] and nodes[u].get('type')=='SINK'
        assert all(int(nodes[v].get('capacity'))>0 for v in used);ownership[q['net_id']].update(used)
    ledger=Counter(v for used in ownership.values() for v in used)
    assert dict(ledger)=={int(k):v for k,v in data['ledger'].items()}
    assert all(c<=int(nodes[v].get('capacity')) for v,c in ledger.items())
    assert {str(n):{str(v):list(p) for v,p in ps.items()} for n,ps in parents.items()}==data['parents']
    compatible=sum(q['net_id'] in dirty for q in retained.values())
    assert (len(queries),len(retained),len(released),unsafe,compatible)==(row['required'],row['retained'],row['released'],row['target_budget_rejected'],row['retained_inside_endpoint_changed_NETs'])
    results.append(dict(width=case['width'],index=case['index'],required=len(queries),retained=len(retained),released=len(released),budget_rejected=unsafe,compatible_branches_retained_inside_changed_NETs=compatible))
assert len(results)==len(r['rows'])==len(protocol['cases'])==12
assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,complete_twelve_cases_independent_branch_forest_pass=True,rows=results,
    scope='Every query partition, unchanged native path, original XML/Fraction delay/current supplied budget, shared parent and unique-NET capacity verified. Retained subset only; missing branches not repaired. No changed-price optimality, packed-pin/incomplete-NET native import, full STA, heldout or time gain proof.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(results,indent=2))
