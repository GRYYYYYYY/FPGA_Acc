"""Prospective graph-only full CHANNEL and inclusive spatial metric domains."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
B=R/'experiments/wbuart_width_frames_v2_2026-10-20/verification.json'
O=R/'experiments/wbuart_quality_domains_v1_2026-10-20'

def main():
    bundle=json.loads(B.read_text());O.mkdir(exist_ok=False)
    for row in bundle['rows']:
        p=Path(row['verification']);frame=json.loads(p.read_text());row.update(endpoint=str(p.parent/'routing_endpoints.json'),graph_sha256=frame['graph_sha256'],graph_nodes=frame['graph_nodes'])
    policy=dict(resource_universe='All capacity-positive CHANX/CHANY, retaining zero demand',resource_score='unique NET occupancy divided by node capacity',resource_k='floor(resource_count/20), at least1; same existing MMC convention',spatial_universe='Every inclusive (layer,x,y,type,segment) bin touched by a positive CHANNEL',spatial_score='sum unique-NET node occupancy over inclusive spans divided by sum node capacities over same spans',spatial_k='min(20,spatial_bin_count)',ties='Descending exact score, then ascending integer RR ID or (layer,x,y,type,integer segment) tuple',spearman='Pearson correlation of average ranks; constant vector yields undefined/null, as existing prediction_metrics.py; undefined primary metric fails the gate; no dropping zero entries',metrics=['resource_spearman','resource_precision_at_top5percent','spatial_spearman','spatial_precision_at_top20'],primary_controls=['previous_native','raw_min_on'],candidate='native_retained_on',gate='Every fixed target case, against each primary control: all4 metrics nonregress and at least1 strictly improves; Spearman epsilon1e-12, exact hit-count comparisons for precision. All9 targets required.',failures='Retain every fixed width/target; unavailable source/warm/prediction/native label is a failed cohort availability gate, no replacement or selective mean',scope='Graph-only metric-domain freeze; not complete executable workflow freeze. No native labels opened.')
    (O/'protocol.json').write_text(json.dumps(dict(policy=policy,bindings={str(B):sha(B),str(Path(__file__).resolve()):sha(__file__)}),indent=2)+'\n')
    rows=[]
    for row in bundle['rows']:
        if row['frame']!='source':continue
        meta=json.loads(Path(row['endpoint']).read_text());graph=Path(meta['inputs']['graph']['path']);digest=sha(graph)
        if digest!=row['graph_sha256']:raise ValueError('graph changed')
        d=O/f"w{row['width']:03d}";d.mkdir();bins=Counter();count=0;nodes=0;stack=[]
        with (d/'resources.jsonl').open('x') as out:
            for event,e in ET.iterparse(graph,events=('start','end')):
                if event=='start':stack.append(e);continue
                parent=stack[-2].tag if len(stack)>1 else None
                if e.tag=='node' and parent=='rr_nodes':
                    if int(e.get('id'))!=nodes:raise ValueError('node index order')
                    nodes+=1;kind=e.get('type');cap=int(e.get('capacity'))
                    if kind in ('CHANX','CHANY') and cap>0:
                        loc=e.find('loc');seg=int(e.find('segment').get('segment_id'));layer=int(loc.get('layer','0'))
                        keys=[(layer,x,y,kind,seg) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)]
                        if not keys:raise ValueError('empty span')
                        bins.update({key:cap for key in keys});count+=1
                        out.write(json.dumps(dict(id=int(e.get('id')),capacity=cap,bins=keys),separators=(',',':'))+'\n')
                if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
                stack.pop()
        if nodes!=row['graph_nodes']:raise ValueError('graph node count')
        (d/'spatial_bins.json').write_text(json.dumps([dict(key=k,capacity=v) for k,v in sorted(bins.items())],separators=(',',':'))+'\n')
        result=dict(width=row['width'],graph_sha256=digest,graph_nodes=nodes,resources=count,resource_k=max(1,count//20),spatial_bins=len(bins),spatial_k=min(20,len(bins)),bindings={str(graph):digest,**{str(p):sha(p) for p in d.iterdir()}})
        (d/'verification.json').write_text(json.dumps(result,indent=2)+'\n');rows.append(result)
        print('QUALITY_DOMAIN',row['width'],count,result['resource_k'],len(bins),flush=True)
    (O/'verification.json').write_text(json.dumps(dict(status='ALL3_GRAPH_ONLY_QUALITY_DOMAINS_FROZEN',policy=policy,rows=rows,bindings={str(O/'protocol.json'):sha(O/'protocol.json')}),indent=2)+'\n')
if __name__=='__main__':main()
