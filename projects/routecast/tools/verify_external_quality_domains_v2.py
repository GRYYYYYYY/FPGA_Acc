"""Independent Expat reconstruction of full CHANNEL and spatial domains."""
import json
from pathlib import Path
from collections import Counter
from xml.parsers import expat
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_quality_domains_v2_2026-10-19'
proof=json.loads((D/'verification.json').read_text());rows=[];bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)}
for row in proof['rows']:
    assert all(sha(p)==h for p,h in row['bindings'].items());bindings.update(row['bindings'])
    graph=next(Path(p) for p,h in row['bindings'].items() if h==row['graph_sha256'])
    d=D/f"w{row['width']:03d}";resources={r['id']:r for r in map(json.loads,(d/'resources.jsonl').read_text().splitlines())}
    stack=[];current=None;bins=Counter();seen=set();node_count=[0]
    def start(tag,attrs):
        global current
        parent=stack[-1] if stack else None
        if tag=='node' and parent=='rr_nodes':
            node_count[0]+=1;current=dict(attrs)
        elif current is not None and tag in ('loc','segment'):current[tag]=dict(attrs)
        stack.append(tag)
    def end(tag):
        global current
        if tag=='node' and len(stack)>1 and stack[-2]=='rr_nodes':
            n=current;current=None;cap=int(n['capacity'])
            if n['type'] in ('CHANX','CHANY') and cap>0:
                nid=int(n['id']);assert nid not in seen;seen.add(nid);loc=n['loc'];segment=int(n['segment']['segment_id'])
                keys=[]
                for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
                    for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
                        key=(int(loc.get('layer','0')),x,y,n['type'],segment);keys.append(list(key));bins[key]+=cap
                assert resources[nid]==dict(id=nid,capacity=cap,bins=keys)
        assert stack.pop()==tag
    p=expat.ParserCreate();p.StartElementHandler=start;p.EndElementHandler=end
    with graph.open('rb') as f:p.ParseFile(f)
    assert seen==set(resources) and len(seen)==row['resources'] and node_count[0]==row['graph_nodes']
    assert row['resource_k']==max(1,len(seen)//20) and row['spatial_k']==min(20,len(bins))
    assert json.loads((d/'spatial_bins.json').read_text())==[dict(key=list(k),capacity=v) for k,v in sorted(bins.items())]
    rows.append(dict(width=row['width'],resources=len(seen),resource_k=row['resource_k'],spatial_bins=len(bins),all_resource_memberships_and_bin_capacities_exact=True))
assert len(rows)==3 and len({r['graph_sha256'] for r in proof['rows']})==3
assert all(sha(p)==h for p,h in bindings.items())
(D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL3_EXPAT_RESOURCE_IDENTITIES_INCLUSIVE_BINS_CAPACITIES_AND_K_EXACT',bindings=bindings,rows=rows,labels_opened=False),indent=2)+'\n')
print('ALL3_INDEPENDENT_QUALITY_DOMAINS_PASS',rows)
