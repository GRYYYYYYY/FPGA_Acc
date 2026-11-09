import json
from pathlib import Path
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_capacity_rc_search import NativeCapacityRC
root=Path(__file__).resolve().parents[1];parent=root/'experiments/nonzero_rc_ex5p_joint_capacity_2026-10-06';r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json');out=root/'experiments/ex5p_frozen_delay_query_2026-10-06';out.mkdir();graph,digest,nodes,f,rc,queries=load_endpoints(root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json');q=r['failure']['query'];own=set();slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])}
for record in r['records']:
 if record['net_id']==q['net_id']:
  own.add(record['source'])
  for eid in record['answer']['physical_edge_ids']:own.add(slots[eid][1])
other={int(n):count-int(int(n) in own) for n,count in r['ledger'].items()};other={n:count for n,count in other.items() if count};(out/'protocol.json').write_text(json.dumps({'parent_sha256':sha(parent/'receipt.json'),'budget_ns':1,'max_labels':10000,'objective':'exact delay increment times other-demand+1; same frozen170-prefix occupancy'},indent=2)+'\n');native=NativeCapacityRC(rc)
for s in range(len(rc.increments)):native.arrays[3][s]=rc.increments[s]
native.set_other(other);answer=native.query(q['source'],q['sink'],rc.scale//10**9,max_labels=10000);result={'query':q,'other':other,'answer':answer,'scale':rc.scale,'graph_sha256':digest,'parent_sha256':sha(parent/'receipt.json'),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(answer['status'],answer['labels_created'])
