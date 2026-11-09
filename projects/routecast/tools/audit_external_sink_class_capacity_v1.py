"""Graph/endpoint-only terminal-class capacity necessity and free pin matching.
No source reachability, native equivalent-pin legality or global routability.
"""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def main():
    bp=R/'experiments/prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';b=json.loads(bp.read_text());out=R/'experiments/prospective_external_family_sink_capacity_v1_2026-10-19';out.mkdir(exist_ok=False);rows=[];bindings={str(bp):sha(bp),str(Path(__file__).resolve()):sha(__file__)}
    for row in b['rows']:
        if row['frame']!='source':continue
        ep=Path(row['endpoint']);m=json.loads(ep.read_text());graph=Path(m['inputs']['graph']['path']);assert sha(graph)==m['graph_sha256'];caps=[];types=[];incoming=defaultdict(set);stack=[]
        for event,e in ET.iterparse(graph,events=('start','end')):
            if event=='start':stack.append(e);continue
            parent=stack[-2].tag if len(stack)>1 else None
            if e.tag=='node' and parent=='rr_nodes':
                assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));types.append(e.get('type'))
            elif e.tag=='edge' and parent=='rr_edges':
                u,v=int(e.get('src_node')),int(e.get('sink_node'))
                if types[v]=='SINK':
                    assert types[u]=='IPIN';incoming[v].add(u)
            if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
            stack.pop()
        demands=defaultdict(dict)
        for q in m['connections']:
            n=q['sink'];assert types[n]=='SINK'
            demands[n].setdefault(q['net_id'],[]).append(q['connection_id'])
        # Disjoint neighborhoods make per-class counts sufficient only for
        # this unconstrained terminal assignment, not for routing to the pins.
        used={};disjoint=True;class_rows=[];violations=[];assignments=[]
        for sink,nets in sorted(demands.items()):
            neighbors=sorted(u for u in incoming[sink] if caps[u]>0);slots=[]
            for u in neighbors:
                if u in used and used[u]!=sink:disjoint=False
                used[u]=sink;slots.extend([u]*caps[u])
            bound=min(caps[sink],len(slots));need=len(nets)
            class_rows.append(dict(sink=sink,distinct_NET_demand=need,sink_capacity=caps[sink],incoming_IPIN_capacity=len(slots),slack=bound-need))
            if need>bound:violations.append(class_rows[-1])
            else:
                for net,pin in zip(sorted(nets),slots):assignments.append(dict(sink=sink,net_id=net,IPIN=pin,connection_ids=nets[net]))
        if disjoint and not violations:
            assigned=Counter(x['IPIN'] for x in assignments);assert all(v<=caps[n] for n,v in assigned.items())
            assert {(x['sink'],x['net_id']) for x in assignments}=={(sink,net) for sink,nets in demands.items() for net in nets}
        proof=dict(width=row['width'],graph_sha256=m['graph_sha256'],demanded_sink_classes=len(demands),required_distinct_NET_class_pairs=sum(map(len,demands.values())),capacity_violations=violations,positive_IPIN_neighborhoods_disjoint=disjoint,free_terminal_assignment_exists=disjoint and not violations,tight_classes=sum(x['slack']==0 for x in class_rows),minimum_class_slack=min(x['slack'] for x in class_rows),classes=class_rows,assignments=assignments if disjoint and not violations else None)
        p=out/f"w{row['width']:03d}.json";p.write_text(json.dumps(proof,separators=(',',':'))+'\n');bindings.update({str(ep):sha(ep),str(graph):sha(graph),str(p):sha(p)});rows.append({k:proof[k] for k in ('width','demanded_sink_classes','required_distinct_NET_class_pairs','free_terminal_assignment_exists','tight_classes','minimum_class_slack')});print('SINK_CLASS_CAPACITY',rows[-1],flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (out/'verification.json').write_text(json.dumps(dict(status='ALL3_SOURCE_TERMINAL_CAPACITY_NECESSITY_AUDITS_COMPLETE',bindings=bindings,rows=rows,scope='SINK and incoming IPIN capacity only; disjoint neighborhoods plus explicit assignment witness check. Assignment ignores SOURCE reachability, channel capacity, pin-equivalence/native packed mapping, perconnection delay budgets and joint routing; no legal source admission.'),indent=2)+'\n')
if __name__=='__main__':main()
