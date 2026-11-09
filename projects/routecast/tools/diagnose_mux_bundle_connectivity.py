"""Check same-span bundle interchangeability through projected physical adjacency."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments/mux_spatial_bundles_2026-10-06';p=json.loads((base/'protocol.json').read_text());r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json')
out=root/'experiments/mux_bundle_connectivity_2026-10-06';out.mkdir();cases=[]
for c,row in zip(p['cases'],r['rows']):
 f=base/f"mux_w{c['data_width']}_c{c['channels']}_bundles.json";assert sha(f)==row['detail_sha256'];cases.append({'data_width':c['data_width'],'channels':c['channels'],'graph':c['graph'],'graph_sha256':c['bindings'][c['graph']],'bundles':str(f),'bundles_sha256':sha(f)})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'source_sha256':sha(Path(__file__)),'scope':'Same-span group adjacency diagnosis. Channel neighbors mapped to same-span bundles; nonchannels retain physical node IDs. Compare incoming/outgoing sets of projected neighbor and switch ID; duplicate edges ignored. Equality is necessary only for this projection, not full interchangeable routes or switch RC equivalence.'},indent=2)+'\n');rows=[]
for c in cases:
 assert sha(c['graph'])==c['graph_sha256'];bs=json.loads(Path(c['bundles']).read_text());membership={i:j for j,b in enumerate(bs) for i in b['nodes']};incoming=defaultdict(set);outgoing=defaultdict(set)
 def target(i):return ('bundle',membership[i]) if i in membership else ('node',i)
 for event,e in ET.iterparse(c['graph'],events=['end']):
  if e.tag!='edge':continue
  a=int(e.get('src_node'));b=int(e.get('sink_node'));sw=int(e.get('switch_id'))
  if a in membership:outgoing[a].add((target(b),sw))
  if b in membership:incoming[b].add((target(a),sw))
  e.clear()
 detail=[]
 for b in bs:
  ids=b['nodes'];ins={frozenset(incoming[i]) for i in ids};outs={frozenset(outgoing[i]) for i in ids};both={(frozenset(incoming[i]),frozenset(outgoing[i])) for i in ids};detail.append({'key':b['key'],'members':len(ids),'incoming_signature_classes':len(ins),'outgoing_signature_classes':len(outs),'joint_signature_classes':len(both)})
 file=out/f"mux_w{c['data_width']}_c{c['channels']}_connectivity.json";file.write_text(json.dumps(detail,indent=2)+'\n');row={'data_width':c['data_width'],'channels':c['channels'],'bundles':len(bs),'multiple_member_bundles':sum(x['members']>1 for x in detail),'projected_incoming_mixed':sum(x['incoming_signature_classes']>1 for x in detail),'projected_outgoing_mixed':sum(x['outgoing_signature_classes']>1 for x in detail),'projected_joint_mixed':sum(x['joint_signature_classes']>1 for x in detail),'detail_sha256':sha(file)};rows.append(row);print(row,flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'complete':len(rows)==9},indent=2)+'\n')
