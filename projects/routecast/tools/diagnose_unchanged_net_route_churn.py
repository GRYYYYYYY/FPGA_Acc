"""Native cold-route churn attribution by observable endpoint-change NET class."""
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[1]
mp=ROOT/'experiments/observable_affected_cells_2026-10-07/evaluation.json';mask_evidence=json.loads(mp.read_text());assert all(sha(p)==h for p,h in mask_evidence['bindings'].items())
protocol=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
rp=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/receipt.json';vp=rp.parent/'verification.json'
r=json.loads(rp.read_text());assert json.loads(vp.read_text())['receipt_sha256']==sha(rp)
cases={(x['width'],x['index']):x for x in json.loads(protocol.read_text())['cases']}
bindings={str(p):sha(p) for p in (mp,protocol,rp,vp,Path(__file__),ROOT/'tools/native_route_ledger_import_compact.py')};contexts={};rows=[]
def sets(path):return {name:{n for branch in branches for n,_ in branch} for name,branches in physical_paths(path).items() if branches}
for x in r['rows']:
    w,i=x['width'],x['index'];case=cases[w,i];assert x['complete'] and x['error'] is None
    old,target=[json.loads(Path(case[k]).read_text()) for k in ('old','target')]
    for key in ('old','target'):
        file=Path(case[key]);assert sha(file)==case['inputs'][str(file)];bindings[str(file)]=sha(file)
    oldrows={q['connection_id']:q for q in old['connections']}
    dirty={target['net_names'][str(q['net_id'])] for q in target['connections'] if (q['source'],q['sink'])!=(oldrows[q['connection_id']]['source'],oldrows[q['connection_id']]['sink'])}
    if w not in contexts:
        graph=Path(old['inputs']['graph']['path']);assert sha(graph)==old['graph_sha256'];bindings[str(graph)]=sha(graph)
        channels={}
        for _,node in ET.iterparse(graph,events=('end',)):
            if node.tag!='node':continue
            if node.get('type') in ('CHANX','CHANY') and int(node.get('capacity'))>0:
                loc=node.find('loc');d=0 if node.get('type')=='CHANX' else 1
                channels[int(node.get('id'))]={(xx,yy,d) for xx in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for yy in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)}
            node.clear()
        oldroute=graph.parent/'design.route';assert sha(oldroute)==mask_evidence['bindings'][str(oldroute)];bindings[str(oldroute)]=sha(oldroute)
        original=sets(oldroute);contexts[w]=channels,original
    channels,original=contexts[w];reload=x['rounds'][0]['reload']
    assert reload['exit_code']==0 and reload['mismatches']==reload['fixups']==0
    route=next(Path(p) for p in reload['files'] if p.endswith('/design.route'));assert sha(route)==reload['files'][str(route)];bindings[str(route)]=sha(route)
    current=sets(route);assert original.keys()==current.keys() and dirty<=current.keys()
    dirty_delta=Counter();stable_delta=Counter();netrows=[]
    for name in sorted(original):
        a,b=original[name]&channels.keys(),current[name]&channels.keys()
        cls=dirty_delta if name in dirty else stable_delta
        for n in b-a:
            for cell in channels[n]:cls[cell]+=1
        for n in a-b:
            for cell in channels[n]:cls[cell]-=1
        netrows.append(dict(name=name,endpoint_changed=name in dirty,channel_union_changed=a!=b,removed_channel_nodes=len(a-b),added_channel_nodes=len(b-a)))
    maskfile=mp.parent/f'w{w}_m{i}_mask.json';assert sha(maskfile)==mask_evidence['bindings'][str(maskfile)];bindings[str(maskfile)]=sha(maskfile)
    mask={tuple(c) for c in json.loads(maskfile.read_text())}
    allcells=set(dirty_delta)|set(stable_delta)
    total={cell:dirty_delta[cell]+stable_delta[cell] for cell in allcells}
    outside={cell for cell,value in total.items() if value and cell not in mask}
    # Signed counts decompose exactly; class absolute masses do not add under cancellation.
    assert all(total[c]==dirty_delta[c]+stable_delta[c] for c in allcells)
    unchanged=[q for q in netrows if not q['endpoint_changed']]
    rows.append(dict(width=w,index=i,total_nets=len(netrows),endpoint_changed_nets=len(dirty),unchanged_endpoint_nets=len(unchanged),unchanged_endpoint_nets_with_channel_change=sum(q['channel_union_changed'] for q in unchanged),dirty_nets_with_channel_change=sum(q['channel_union_changed'] for q in netrows if q['endpoint_changed']),outside_changed_cells=len(outside),outside_cells_with_unchanged_net_delta=sum(stable_delta[cell]!=0 for cell in outside),outside_cells_with_changed_net_delta=sum(dirty_delta[cell]!=0 for cell in outside),changed_net_delta_absolute_mass=sum(abs(v) for v in dirty_delta.values()),unchanged_net_delta_absolute_mass=sum(abs(v) for v in stable_delta.values()),total_delta_absolute_mass=sum(abs(v) for v in total.values()),nets=netrows))
assert len(rows)==12 and all(sha(p)==h for p,h in bindings.items())
out=ROOT/'experiments/unchanged_net_route_churn_2026-10-07';out.mkdir(exist_ok=False)
report=dict(bindings=bindings,rows=rows,scope='12 archived original vs independently cold-routed target native canonical routes. NET name joins; channel union changes only, not full path/switch identity. Exact signed count decomposition, class absolute masses may cancel and cannot be added. Churn is cold-router variability plus placement effects, not causal proof of incremental-router mandatory reroutes. Endpoint-stable route prior is not locality guarantee. No new routing, prospective/heldout or netgain.')
(out/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n')
print([(q['width'],q['index'],q['unchanged_endpoint_nets_with_channel_change'],q['unchanged_endpoint_nets'],q['outside_changed_cells'],q['outside_cells_with_unchanged_net_delta']) for q in rows])
