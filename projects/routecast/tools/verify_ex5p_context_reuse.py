"""Independently reconstruct frozen demand directly from original XML edge endpoints."""
import json,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_context_reuse_2026-10-06'
def read(p):return json.loads(p.read_text())
p=read(out/'protocol.json');r=read(out/'receipt.json');fixtures=read(out/'fixtures.json');parent=root/'experiments/nonzero_rc_ex5p_joint_delay_2026-10-06';base=read(parent/'receipt.json');ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';e=read(ep)
assert sha(parent/'receipt.json')==p['parent_sha256'] and sha(parent/'verification.json')==p['proof_sha256']
assert sha(ep)==p['endpoint_sha256'] and sha(out/'protocol.json')==r['protocol_sha256'] and sha(out/'fixtures.json')==r['fixture_sha256'] and sha(root/'tools/trial_ex5p_context_reuse.py')==r['source_sha256']
g=Path(e['inputs']['graph']['path']);assert sha(g)==base['graph_sha256'];xml=ET.parse(g).getroot();edges=list(xml.find('rr_edges'));unions=defaultdict(set);ledger=Counter()
for i,a in enumerate(base['attempts']):
 q=a['query'];net=q['net_id']
 if i in p['indices']:
  other=dict(ledger)
  for n in unions[net]:other[n]-=1
  x=fixtures[str(i)];assert x['query']==q and x['expected']==a['native_answer'] and {int(n):c for n,c in x['other'].items()}=={n:c for n,c in other.items() if c}
 if i<len(base['records']):
  rec=base['records'][i];used={rec['source']};node=rec['source']
  for eid in rec['answer']['physical_edge_ids']:
   edge=edges[eid];assert int(edge.get('src_node'))==node;node=int(edge.get('sink_node'));used.add(node)
  assert node==rec['sink'];ledger.update(used-unions[net]);unions[net].update(used)
assert [x['index'] for x in r['rows']]==p['reuse_order']
for x in r['rows']:
 assert x['answer']==fixtures[str(x['index'])]['expected']
 assert all(x[k]>0 for k in ('fresh_context_s','fresh_query_s','reused_query_s'))
result={'receipt_sha256':sha(out/'receipt.json'),'independent_XML_frozen_demand_verified':True,'queries':len(r['rows']),'full_native_answers_equal':True,'fresh_context_total_s':sum(x['fresh_context_s'] for x in r['rows']),'reused_initial_context_s':r['reused_initial_context_s'],'fresh_query_total_s':sum(x['fresh_query_s'] for x in r['rows']),'reused_query_total_s':sum(x['reused_query_s'] for x in r['rows']),'scope':'Demand reconstructed from original XML. Answer parity with authenticated previously independently audited prefix/cut. Six frozen queries only, no full workflow speedup claim.'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
