"""Frozen-query fresh/reused context comparison; no route or policy changes."""
import json,time
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_capacity_rc_search import NativeCapacityRC
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_context_reuse_2026-10-06';out.mkdir()
parent=root/'experiments/nonzero_rc_ex5p_joint_delay_2026-10-06';r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json')
ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json'
indices=[0,169,1171];order=[1171,0,169,0,1171,169]
(out/'protocol.json').write_text(json.dumps({'parent_sha256':sha(parent/'receipt.json'),'proof_sha256':sha(parent/'verification.json'),'endpoint_sha256':sha(ep),'indices':indices,'reuse_order':order,'budget_ns':1,'max_labels':10000,'policy':'Freeze original prefix otherNET state; compare fresh and reused exact-delay native answers including labels/cost/path, interleave empty/loaded demand and restore cost after temporary mutation. No rerouting/quality or net acceleration claim.'},indent=2)+'\n')
def context():
 start=time.monotonic();g,d,n,f,rc,q=load_endpoints(ep);native=NativeCapacityRC(rc)
 for s,x in enumerate(rc.increments):native.arrays[3][s]=x
 return f,rc,native,time.monotonic()-start
f,rc,native,initial=context();slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(len(f['node_ids'])) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};unions=defaultdict(set);ledger=Counter();fixtures={}
for i,a in enumerate(r['attempts']):
 q=a['query'];net=q['net_id']
 if i in indices:
  other=dict(ledger)
  for n in unions[net]:other[n]-=1
  fixtures[i]={'query':q,'other':{n:c for n,c in other.items() if c},'expected':a['native_answer']}
 if i<len(r['records']):
  rec=r['records'][i];used={rec['source']}
  for eid in rec['answer']['physical_edge_ids']:used.add(slots[eid][1])
  ledger.update(used-unions[net]);unions[net].update(used)
assert set(fixtures)==set(indices)
(out/'fixtures.json').write_text(json.dumps(fixtures,indent=2)+'\n');rows=[]
for i in order:
 x=fixtures[i];q=x['query'];freshf,freshrc,fresh,setup=context();start=time.monotonic();fresh.set_other(x['other']);a=fresh.query(q['source'],q['sink'],freshrc.scale//10**9,max_labels=10000);freshquery=time.monotonic()-start
 # Restore mutable costs explicitly before reusing the shared demand buffer.
 native.arrays[3][0]=0
 native.arrays[3][0]=rc.increments[0]
 start=time.monotonic();native.set_other(x['other']);b=native.query(q['source'],q['sink'],rc.scale//10**9,max_labels=10000);reusequery=time.monotonic()-start
 assert a==b==x['expected'];assert {n:c for n,c in enumerate(native.other) if c}==x['other']
 rows.append({'index':i,'fresh_context_s':setup,'fresh_query_s':freshquery,'reused_query_s':reusequery,'answer':b})
result={'rows':rows,'reused_initial_context_s':initial,'answers_exact':True,'protocol_sha256':sha(out/'protocol.json'),'fixture_sha256':sha(out/'fixtures.json'),'source_sha256':sha(Path(__file__)),'scope':'Six frozen-query replays only, complete original native answers equal; no full workflow speed or generalization result.'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2));print('fresh setup total',sum(x['fresh_context_s'] for x in rows),'reuse queries total',sum(x['reused_query_s'] for x in rows))
