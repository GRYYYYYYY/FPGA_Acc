"""Capacity-positive directed reachability, independent of native route trees/costs."""
import json, shutil, time
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import extract, sha
from nonclock_global_pins import classify


def main():
    root = Path(__file__).resolve().parents[1]
    capture = root/'experiments/multiplier_family_native_capture_cw64_2026-10-06'
    out = root/'experiments/multiplier_cw64_reachability_2026-10-06'
    out.mkdir()
    (out/'sources').mkdir()
    for name in ('audit_narrow_channel_reachability_cw64.py', 'pre_route_endpoints.py', 'nonclock_global_pins.py'):
        shutil.copyfile(root/'tools'/name, out/'sources'/name)
    cp = json.loads((capture/'protocol.json').read_text())
    receipt = json.loads((capture/'receipt.json').read_text())
    assert sha(capture/'protocol.json') == receipt['protocol_sha256']
    protocol = {'capture_receipt_sha256':sha(capture/'receipt.json'),
                'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},
                'cohort':cp['cohort'], 'policy':'all retained pre-route class endpoints; directed XML edges with both endpoints capacity > 0; exhaustive per-source traversal, no cost or occupancy limits',
                'scope':'Necessary relaxed reachability condition only. Reachable does not prove simultaneous routability, pin feasibility, or electrical validity; unreachable forbids a directed capacity-positive path for these extracted class endpoints.'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    results=[]
    for case in receipt['results']:
        start=time.monotonic();name=case['design'];art=case['artifacts'];dest=out/name;dest.mkdir()
        required=('design.net','design.place','rr_graph.xml')
        assert all(sha(art[k]['path']) == art[k]['sha256'] for k in required)
        ep,mapping=extract(art['design.net']['path'],art['design.place']['path'],art['rr_graph.xml']['path'])
        global_ids={r['net_id'] for r in classify(mapping,art['design.net']['path'],cp['architecture']['path'],art['rr_graph.xml']['path'])}
        ep['connections']=[r for r in ep['connections'] if r['net_id'] not in global_ids]
        (dest/'endpoints.json').write_text(json.dumps(ep)+'\n');(dest/'mapping.json').write_text(json.dumps(mapping)+'\n')
        capacity={};adj=defaultdict(list);stack=[]
        for event,e in ET.iterparse(art['rr_graph.xml']['path'],events=('start','end')):
            if event=='start':stack.append(e);continue
            parent=stack[-2].tag if len(stack)>1 else None
            if e.tag=='node' and parent=='rr_nodes':capacity[int(e.get('id'))]=int(e.get('capacity'))
            if e.tag=='edge' and parent=='rr_edges':
                a,b=int(e.get('src_node')),int(e.get('sink_node'))
                assert a in capacity and b in capacity
                if capacity[a]>0 and capacity[b]>0:adj[a].append(b)
            if parent in ('rr_nodes','rr_edges','switches','segments','block_types','grid','channels'):stack[-2].remove(e);e.clear()
            stack.pop()
        groups=defaultdict(list)
        for r in ep['connections']:groups[r['source']].append(r)
        failures=[]
        for source,connections in groups.items():
            seen={source} if capacity[source]>0 else set();pending=list(seen)
            while pending:
                for sink in adj.get(pending.pop(),()):
                    if sink not in seen:seen.add(sink);pending.append(sink)
            failures.extend(r for r in connections if r['sink'] not in seen)
        assert all(sha(art[k]['path']) == art[k]['sha256'] for k in required)
        result={'design':name,'connections':len(ep['connections']),'sources':len(groups),'unreachable_connections':failures,'unreachable_count':len(failures),'graph_sha256':ep['graph_sha256'],'case_receipt_sha256':sha(capture/(name+'_receipt.json')),'endpoints_sha256':sha(dest/'endpoints.json'),'mapping_sha256':sha(dest/'mapping.json'),'wall_s':time.monotonic()-start}
        (dest/'report.json').write_text(json.dumps(result,indent=2)+'\n');results.append(result)
        print(json.dumps({k:result[k] for k in ('design','connections','unreachable_count','wall_s')}),flush=True)
    assert all(sha(out/'sources'/name)==h for name,h in protocol['sources'].items())
    (out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':results,'reports':{r['design']:sha(out/r['design']/'report.json') for r in results}},indent=2)+'\n')

if __name__=='__main__':main()
