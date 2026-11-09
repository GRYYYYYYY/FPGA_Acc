"""Compare exposed target native paths against frozen model proxy budgets.
Static additive delay only, not STA slack, irreducibility or a budget retuning.
"""
import json,xml.etree.ElementTree as ET
from fractions import Fraction
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_supplementary_development_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
    out=R/'experiments/prospective_external_family_native_budget_compatibility_v1_2026-10-19';out.mkdir(exist_ok=False)
    sp=D/'specifications/w160/episode_01/comparison_spec.json';spec=read(sp);meta=read(spec['endpoint']);graph=Path(meta['inputs']['graph']['path']);switches={};stack=[];nodes=0
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if e.tag=='node' and parent=='rr_nodes':
            assert int(e.get('id'))==nodes;nodes+=1;t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
        elif e.tag=='switch' and parent=='switches':
            t=e.find('timing');assert all(Fraction(t.get(k,'0'))==0 for k in ('R','Cin','Cout','Cinternal'));v=Fraction(t.get('Tdel','0'))*10**18;assert v.denominator==1 and v>=0;switches[int(e.get('id'))]=v.numerator
        if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
        stack.pop()
    bindings={str(graph):sha(graph),str(Path(__file__).resolve()):sha(__file__)};rows=[]
    source_path=Path(spec['source_frame']);source=read(source_path);old={r['connection_id']:r for r in source['records']};assert source['scale']==10**18;bindings[str(source_path)]=sha(source_path)
    for episode in range(1,4):
        case=f'w160/episode_{episode:02d}';spec_path=D/'specifications'/case/'comparison_spec.json';s=read(spec_path);ep=read(s['endpoint']);warm_dir=D/'predictions'/case/'warm/native_retained';wp=warm_dir/'verification.json';proof=read(wp);dirty=set(proof['dirty_nets']);frame_path=warm_dir/'initial.json';frame=read(frame_path);records={r['connection_id']:r for r in frame['records']};assert frame['scale']==source['scale'] and ep['graph_sha256']==source['graph_sha256']==sha(graph)
        admission=read(s['label_proof']);assert admission['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';assert all(sha(p)==h for p,h in admission['bindings'].items());route=Path(s['label_physical_audit']).parent/'output.route'
        observed={}
        for name,paths in physical_paths(route).items():
            for path in paths:
                key=name,path[0][0],path[-1][0];assert key not in observed;observed[key]=path
        groups=defaultdict(list);details=[];nets=defaultdict(set)
        for q in ep['connections']:
            cid=q['connection_id'];key=ep['net_names'][str(q['net_id'])],q['source'],q['sink'];path=observed.pop(key);assert path[0][1] is None
            delay=sum(switches[switch] for node,switch in path[1:]);record=records[cid];budget=record['budget_integer'];floor=record['floor_integer'];assert type(budget) is int and delay>=floor>=0
            changed=(q['source'],q['sink'])!=(old[cid]['source'],old[cid]['sink']);group='direct_endpoint_change' if changed else 'unchanged_sibling_in_dirty_NET' if q['net_id'] in dirty else 'clean_NET'
            item=dict(connection_id=cid,net_id=q['net_id'],group=group,target_native_additive_delay=delay,budget_integer=budget,raw_floor_integer=floor,source_native_additive_delay=old[cid]['answer']['delay'],exceeds_frozen_budget=delay>budget,excess=max(0,delay-budget));details.append(item);groups[group].append(item)
            if delay>budget:nets[group].add(q['net_id'])
        assert not observed and len(details)==len(old)==15616
        summary={}
        for name,items in groups.items():
            summary[name]=dict(connections=len(items),violations=sum(x['exceeds_frozen_budget'] for x in items),affected_NETs=len(nets[name]),total_positive_excess=sum(x['excess'] for x in items),maximum_excess=max(x['excess'] for x in items),maximum_delay=max(x['target_native_additive_delay'] for x in items))
        row=dict(case=case,groups=summary,total_connections=len(details),total_violations=sum(x['exceeds_frozen_budget'] for x in details),fractional_unit_seconds='1e-18',violating_NETs=len({x['net_id'] for x in details if x['exceeds_frozen_budget']}));rows.append(row)
        p=out/f'episode_{episode:02d}_connections.json';p.write_text(json.dumps(details,separators=(',',':'))+'\n')
        for path in [spec_path,Path(s['endpoint']),wp,frame_path,Path(s['label_proof']),route,p]:bindings[str(path)]=sha(path)
        print('NATIVE_BUDGET_COMPATIBILITY',json.dumps(row),flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (out/'verification.json').write_text(json.dumps(dict(status='ALL46848_EXPOSED_NATIVE_CONNECTION_DELAYS_COMPARED_WITH_FROZEN_PROXY_BUDGETS',bindings=bindings,rows=rows,scope='Zero-R/C original graph and exact integer switch delays, printed native paths already physically admitted. Exceeding budget shows this particular target path is outside model search constraints; does not prove no alternative within-budget route/density, explain causally all metric loss, justify budget relaxation or establish physical STA.'),indent=2)+'\n')
if __name__=='__main__':main()
