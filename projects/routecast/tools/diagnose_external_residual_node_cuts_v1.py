"""Single-forbidden-node reachability of all paths using six residual resources.
These are individual connectivity witnesses, not jointly legal reroutes.
"""
import json,xml.etree.ElementTree as ET
from array import array
from collections import defaultdict,deque
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_executable_development_v1_2026-10-19'
def main():
    ap=D/'failed_source_physical_audit_v1.json';a=json.loads(ap.read_text());row=next(r for r in a['rows'] if r['width']==160);bad={r['node']:r for r in row['overused_nodes']};m=json.loads((D/'native_manifest.json').read_text());job=next(r for r in m['cases'] if r['case']=='w160/source');ep=Path(job['endpoint']);meta=json.loads(ep.read_text());graph=Path(meta['inputs']['graph']['path']);route=Path(job['output'])/'output.route'
    bindings={str(p):sha(p) for p in [ap,ep,graph,route,Path(__file__).resolve()]};assert sha(graph)==meta['graph_sha256']
    impacted=defaultdict(list)
    for name,paths in physical_paths(route).items():
        for path in paths:
            members={n for n,s in path}
            for node in members & bad.keys():impacted[node].append((name,path[0][0],path[-1][0]))
    caps=array('I');us=array('I');vs=array('I');stack=[]
    for event,e in ET.iterparse(graph,events=('start','end')):
        if event=='start':stack.append(e);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if e.tag=='node' and parent=='rr_nodes':
            assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')))
        if e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')))
        if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
        stack.pop()
    # Build adjacency with original XML edge identity, independent of source order.
    offsets=array('I',[0])*(len(caps)+1)
    for u in us:offsets[u+1]+=1
    for n in range(len(caps)):offsets[n+1]+=offsets[n]
    cursor=array('I',offsets);dest=array('I',[0])*len(us);eids=array('I',[0])*len(us)
    for eid,(u,v) in enumerate(zip(us,vs)):
        slot=cursor[u];cursor[u]+=1;dest[slot]=v;eids[slot]=eid
    results=[]
    for forbidden in sorted(bad):
        groups=defaultdict(list)
        for name,source,sink in impacted[forbidden]:groups[source].append((name,sink))
        witnesses=[]
        for source,queries in groups.items():
            pending={sink for _,sink in queries};parents={source:None};queue=deque([source])
            while queue and pending:
                u=queue.popleft();pending.discard(u)
                for slot in range(offsets[u],offsets[u+1]):
                    v=dest[slot]
                    if v!=forbidden and caps[v]>0 and v not in parents:parents[v]=(u,eids[slot]);queue.append(v)
            for name,sink in queries:
                edges=None
                if sink in parents:
                    edges=[];u=sink;seen=set()
                    while u!=source:
                        assert u!=forbidden and u not in seen;seen.add(u);previous,eid=parents[u];assert us[eid]==previous and vs[eid]==u and caps[u]>0;edges.append(eid);u=previous
                    edges.reverse()
                witnesses.append(dict(net_name=name,source=source,sink=sink,reachable_without_node=edges is not None,alternative_original_XML_edge_ids=edges))
        r=dict(forbidden_node=forbidden,type=bad[forbidden]['type'],impacted_printed_connections=len(impacted[forbidden]),queries=len(witnesses),all_individually_avoidable=all(x['reachable_without_node'] for x in witnesses),witnesses=witnesses);results.append(r);print('SINGLE_NODE_CUT',forbidden,r['queries'],r['all_individually_avoidable'],flush=True)
    assert all(sha(p)==h for p,h in bindings.items())
    (D/'residual_node_cut_diagnostics_v1.json').write_text(json.dumps(dict(status='SIX_RESIDUAL_SINGLE_NODE_CONNECTIVITY_CHECKS_COMPLETE',bindings=bindings,rows=results,scope='All printed paths affected by the six observed width160 residual nodes; positive-capacity connectivity in original graph with one resource removed. Individually avoidable is not joint routability, budget/STA/weighted optimality, native continuation success or legal source admission.'),indent=2)+'\n')
if __name__=='__main__':main()
