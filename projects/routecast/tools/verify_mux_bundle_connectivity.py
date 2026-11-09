"""Recompute projected adjacency classes from full XML and frozen memberships."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/mux_bundle_connectivity_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['complete'] and len(r['rows'])==9 and r['protocol_sha256']==sha(out/'protocol.json') and p['source_sha256']==sha(root/'tools/diagnose_mux_bundle_connectivity.py');rows=[]
for c,row in zip(p['cases'],r['rows']):
 assert sha(c['graph'])==c['graph_sha256'] and sha(c['bundles'])==c['bundles_sha256'];bs=json.loads(Path(c['bundles']).read_text());mapping={i:j for j,b in enumerate(bs) for i in b['nodes']};x=ET.parse(c['graph']).getroot();ins=defaultdict(list);outs=defaultdict(list)
 def proj(i):return ('bundle',mapping[i]) if i in mapping else ('node',i)
 for e in x.find('rr_edges'):
  a=int(e.get('src_node'));b=int(e.get('sink_node'));s=int(e.get('switch_id'));outs[a].append((proj(b),s));ins[b].append((proj(a),s))
 expected=[]
 for b in bs:
  signatures=[(tuple(sorted(set(ins[i]))),tuple(sorted(set(outs[i])))) for i in b['nodes']];expected.append({'key':b['key'],'members':len(signatures),'incoming_signature_classes':len({a for a,b in signatures}),'outgoing_signature_classes':len({b for a,b in signatures}),'joint_signature_classes':len(set(signatures))})
 f=out/f"mux_w{c['data_width']}_c{c['channels']}_connectivity.json";assert sha(f)==row['detail_sha256'] and json.loads(f.read_text())==expected
 assert len(expected)==row['bundles'];assert sum(x['members']>1 for x in expected)==row['multiple_member_bundles']
 for side in ['incoming','outgoing','joint']:assert sum(x[side+'_signature_classes']>1 for x in expected)==row['projected_'+side+'_mixed']
 rows.append({'data_width':c['data_width'],'channels':c['channels'],'bundles_verified':len(expected)});print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'Projected neighbor/switch classes independently recomputed; no native routability or complete graph-automorphism proof.'},indent=2)+'\n')
