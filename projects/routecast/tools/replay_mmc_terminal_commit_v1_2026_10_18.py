"""Persisted transition replay using direct XML tail destinations and epochs.

Full path/objective proofs transfer only through exact admitted record equality.
Independent connection ledger is updated from physical XML tail node deltas;
unique-NET ledger uses previously independently audited finite NET patterns.
"""
import json,sys,hashlib
from pathlib import Path
from collections import Counter
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 d=R/'experiments/mmc_terminal_batch_commit_v2_2026-10-18'
 receipt=json.loads((d/'receipt.json').read_text());bindings={**receipt['bindings'],str(d/'receipt.json'):sha(d/'receipt.json'),**closure([Path(__file__)])}
 protocol=json.loads((d/'protocol.json').read_text());out=R/'experiments/mmc_terminal_commit_replay_v1_2026-10-18';out.mkdir()
 summaries=[];cache=Cache()
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  states={};needed=set();graphs=set()
  for case,data in protocol['inputs'].items():
   old=json.loads(Path(data['frame']).read_text());new=json.loads((d/case/'frame.json').read_text());event=json.loads((d/case/'event.json').read_text())
   admitted=json.loads((R/'experiments/mmc_objective_terminal_subset_v1_2026-10-18'/(case+'.json')).read_text())
   updates={r['connection_id']:r for r in admitted['chosen_replacements']}
   assert new['records']==[updates.get(r['connection_id'],r) for r in old['records']]
   changed=[(a,b) for a,b in zip(old['records'],new['records']) if a!=b]
   for a,b in changed:
    assert {k:v for k,v in a.items() if k!='answer'}=={k:v for k,v in b.items() if k!='answer'}
    assert len(a['answer']['physical_edge_ids'])==len(b['answer']['physical_edge_ids'])
    assert a['answer']['physical_edge_ids'][:-3]==b['answer']['physical_edge_ids'][:-3]
    needed.update(a['answer']['physical_edge_ids'][-3:]);needed.update(b['answer']['physical_edge_ids'][-3:])
   endpoint=json.loads(Path(data['endpoint']).read_text());graphs.add(endpoint['inputs']['graph']['path'])
   states[case]=(old,new,event,admitted,changed)
  assert len(graphs)==1;graph=Path(next(iter(graphs)));assert str(graph) in bindings
  mapping={};index=0;stack=[]
  for action,element in ET.iterparse(graph,events=('start','end')):
   if action=='start':stack.append(element);continue
   if element.tag=='edge' and len(stack)>1 and stack[-2].tag=='rr_edges':
    if index in needed:mapping[index]=(int(element.get('src_node')),int(element.get('sink_node')))
    index+=1
   stack.pop()
   if stack:stack[-1].remove(element)
   element.clear()
  assert mapping.keys()==needed
  for case,(old,new,event,admitted,changed) in states.items():
   changed_nets={str(a['net_id']) for a,b in changed};epochs=dict(old['epochs'])
   for net in changed_nets:epochs[net]+=1
   assert new['epochs']==epochs and event['changed_NETs']==sorted(map(int,changed_nets)) and event['changed_queries']==len(changed)
   assert all(old['epochs'][net]==epoch for net,epoch in event['expected_epochs'].items())
   independent=Counter({int(p):n for p,n in old['independent_connection_ledger'].items()})
   for a,b in changed:
    tails=[r['answer']['physical_edge_ids'][-3:] for r in [a,b]]
    assert mapping[tails[0][0]][0]==mapping[tails[1][0]][0]
    for tail in tails:
     assert all(mapping[x][1]==mapping[y][0] for x,y in zip(tail,tail[1:])) and mapping[tail[-1]][1]==a['sink']
    independent.subtract(mapping[e][1] for e in tails[0]);independent.update(mapping[e][1] for e in tails[1])
   assert all(n>=0 for n in independent.values())
   assert {p:n for p,n in independent.items() if n}=={int(p):n for p,n in new['independent_connection_ledger'].items() if n}
   finite=json.loads((R/'experiments/mmc_global_terminal_subset_v1_2026-10-18'/(case+'.json')).read_text())
   masks={}
   for p in finite['NET_patterns']:masks[p['net_id']]=masks.get(p['net_id'],0)|p['mask']
   selected=admitted['summary']['chosen_mask'];ledger=Counter({int(p):n for p,n in old['ledger'].items()})
   for p in finite['NET_patterns']:
    if p['mask']!=selected&masks[p['net_id']]:continue
    assert p['valid'];ledger.update(p['added']);ledger.subtract(p['removed'])
   assert all(n>=0 for n in ledger.values())
   assert {p:n for p,n in ledger.items() if n}=={int(p):n for p,n in new['ledger'].items() if n}
   allowed={'records','ledger','independent_connection_ledger','epochs','overflow_units','eligible_for_legal_route_commit','scope','batch_update_policy'}
   assert {k:v for k,v in old.items() if k not in allowed}=={k:v for k,v in new.items() if k not in allowed}
   assert not new['eligible_for_legal_route_commit'] and new['overflow_units']==admitted['summary']['proposal_overflow']
   canonical=lambda frame:hashlib.sha256(json.dumps(frame,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
   assert canonical(old)==event['source_model_digest'] and canonical(new)==event['model_digest'] and event['generation']==1
   assert event['source_frame_sha256']==sha(protocol['inputs'][case]['frame']) and event['committed_frame_sha256']==sha(d/case/'frame.json')
   summary=dict(case=case,queries_preserved=len(new['records']),changed_queries=len(changed),changed_NET_epochs=len(changed_nets),both_ledgers_replayed=True,overflow=new['overflow_units'])
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (out/'verification.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,summaries=summaries,direct_XML_edges_scanned=index,physical_tail_edges_verified=len(mapping),scope='Persisted records exactly equal independently full-audited candidate, epochs/CAS digest and immutable metadata checked; directXML connection-ledger deltas and prior independently audited NET-pattern ledger replay. No native route or forecast/full-flow gain.'),stream,indent=2)

if __name__=='__main__':main()
