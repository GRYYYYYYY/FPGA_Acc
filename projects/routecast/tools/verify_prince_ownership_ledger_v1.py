"""Offline native update-event replay -> actual connection trees and phase ledgers."""
import json,struct,mmap
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_ownership_ledger_trial_v1_2026-10-20'
def owner_payload(path):
 raw=path.read_bytes();assert raw[:8]==b'RCOWN001';i,count=struct.unpack_from('<QQ',raw,8);off=24;result={}
 for _ in range(count):
  net,endpoint,n=struct.unpack_from('<QQQ',raw,off);off+=24;result[net]=set(struct.unpack_from('<'+'Q'*n,raw,off));off+=8*n
 assert off==len(raw);return i,result
def main():
 vp=D/'verification.json';v=json.loads(vp.read_text());assert len(v['rows'])==18 and all(x['callback_sequence_complete'] and x['nonclock_iteration_summaries_equal'] and x['terminal_physical_sequences_equal'] for x in v['rows']);priorp=R/'experiments/prince_connection_query_trial_v1_2026-10-20/connection_query_verification_v1.json';prior={x['case']:x for x in json.loads(priorp.read_text())['rows']};bindings={str(vp):sha(vp),str(priorp):sha(priorp),str(__file__):sha(__file__)};rows=[]
 for case in sorted(x['case'].rsplit('/',1)[0] for x in v['rows'] if x['case'].endswith('/capture')):
  d=D/case/'capture';receipt=next(x for x in v['rows'] if x['case']==case+'/capture');resources=R/'experiments/prince_quality_domains_v1_2026-10-20'/case.split('/')[0]/'resources.jsonl';domain={x['id'] for x in map(json.loads,resources.open())};cp=d/'queries.tsv.connections.tsv';contexts={int(x[1]):tuple(map(int,x)) for x in (line.split() for line in cp.open())};summary=[list(map(int,line.split())) for line in (d/'queries.tsv').read_text().splitlines()];assert len(summary)==receipt['iterations'];assert sum(x[1] for x in summary)==prior[case]['cost_calls'];assert len(contexts)==prior[case]['connections'];lp=d/'queries.tsv.ledger.bin';owners={};epoch=0;updates=entries=boundaries=adds=removes=owner_checks=node_checks=0;seen=set()
  with lp.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
   off=0
   def word():
    nonlocal off
    x=struct.unpack_from('<Q',data,off)[0];off+=8;return x
   def nodes():
    nonlocal off
    n=word();result=set(struct.unpack_from('<'+'Q'*n,data,off));off+=n*8;assert len(result)==n and result<=domain;return result
   while off<len(data):
    tag=word();e=word()
    if tag==1:
     assert e==epoch+1;epoch=e;net=word();sign=word();group=nodes();own=owners.setdefault(net,set());assert sign in [0,1]
     if sign:assert not own&group;own.update(group);adds+=len(group)
     else:assert group<=own;own.difference_update(group);removes+=len(group)
     updates+=1
    elif tag==2:
     assert e==epoch;ident,net,pin,sink=word(),word(),word(),word();actual=nodes();assert actual==owners.setdefault(net,set());assert ident not in seen;seen.add(ident);context=contexts[ident];assert context[0]==boundaries+1 and context[2:5]==(net,pin,sink);assert context[5]>=len(actual);entries+=1
    elif tag==3:
     assert e==epoch;i=word();assert i==boundaries+1;op=d/'owners'/f'owners_{i}.bin';ii,expected=owner_payload(op);assert ii==i;assert {net:nodes for net,nodes in owners.items() if nodes}=={net:nodes for net,nodes in expected.items() if nodes};owner_checks+=len(expected);counts=Counter(node for group in owners.values() for node in group);rrp=d/'boundary'/f'iteration_{i}.bin';raw=rrp.read_bytes();rr={node:occ for node,kind,occ,cap,acc in struct.iter_unpack('<QIiiI',raw[24:]) if kind in [4,5]};assert set(rr)==domain and all(counts[n]==rr[n] for n in domain);node_checks+=len(domain);boundaries+=1
     for path in [op,rrp]:assert sha(path)==receipt['files'][str(path)];bindings[str(path)]=sha(path)
    else:raise AssertionError(('unknown record tag',tag))
   assert off==len(data)
  assert seen==contexts.keys() and boundaries==receipt['iterations'];assert adds>removes>0
  for path in [lp,cp,d/'queries.tsv']:assert sha(path)==receipt['files'][str(path)];bindings[str(path)]=sha(path)
  bindings[str(resources)]=sha(resources);row=dict(case=case,update_events=updates,connection_entry_replays=entries,boundaries=boundaries,CHANNEL_owner_additions=adds,CHANNEL_owner_removals=removes,NET_boundary_owner_checks=owner_checks,CHANNEL_boundary_occupancy_checks=node_checks,native_cost_calls=sum(x[1] for x in summary),CHANNEL_query_runtime_ledger_checks=sum(x[2] for x in summary),entry_tree_owned_CHANNEL_cost_calls=sum(x[3] for x in summary));rows.append(row);print('OWNERSHIP_LEDGER_CASE_PASS',case,entries,updates,flush=True)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());out=D/'ledger_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='INDEPENDENT_UPDATE_EVENT_REPLAY_MATCHES_ALL_CONNECTION_TREES_AND_PHASE_OWNERS',rows=rows,bindings=bindings,scope='Offline replay of native tree-add/remove node events exactly matches copied entry CHANNEL sets and every phase full NET owner/CHANNEL occupancy payload. At runtime all observed CHANNEL cost queries assert current ledger occupancy and owner membership equality. No independent offline per-query replay (only summary counters), no all-inlined-path coverage or predictive/native/fullpaid gain.'),indent=2)+'\n')
if __name__=='__main__':main()
