"""All-run staging bytes, independent full native demand arrays and final XML paths."""
import json,hashlib
from array import array
from collections import Counter,defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_workflow_screened2_resident_live_staging_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['complete'] and r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items());rows=[]
for case,row in zip(p['cases'],r['rows']):
 n=case['count'];assert row['count']==n and all(sha(f)==h for f,h in case['bindings'].items());work=out/f'n{n}';ep=json.loads(Path(case['target']).read_text());old=json.loads(Path(case['old']).read_text());graph=Path(ep['inputs']['graph']['path']);a=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph);byname={name:int(net) for net,name in old['net_names'].items()};seed=defaultdict(set);net=None
 for line in (Path(case['source'])/'design.route').read_text().splitlines():
  match=NET.match(line)
  if match:net=byname[match[2]]
  match=NODE.match(line)
  if match:seed[net].add(int(match[1]))
 updates=[];query_count=0
 for k,run in enumerate(row['runs']):
  file=work/f"run{k}_{run['model']}.json";assert sha(file)==run['update_sha256'] and run['rollback_verified'];updates.append(file.read_bytes());update=json.loads(file.read_text());initial=update['incremental'];unions=defaultdict(set,{net:set(used) for net,used in seed.items() if net not in initial['affected']['affected_net_ids']});ledger=Counter(node for used in unions.values() for node in used);journal=json.loads((work/f'run{k}_demands.json').read_text());assert sha(work/f'run{k}_demands.json')==run['demands_sha256'];assert update['repair'] is None,'Repair trace requires separate audit extension, do not silently skip';assert len(journal)==len(initial['events'])
  for event,entry in zip(initial['events'],journal):
   q=event['query'];assert entry['source']==q['source'] and entry['sink']==q['sink'];full=array('Q',[0])*len(a.caps)
   for node,value in ledger.items():full[node]=value-int(node in unions[q['net_id']])
   assert hashlib.sha256(full.tobytes()).hexdigest()==entry['digest'];assert event['wire_owner_union']==sorted(unions[q['net_id']]);query_count+=1
   if event['committed']:
    used={q['source']}
    for eid in event['answer']['physical_edge_ids']:
     edge=a.graph.edges[eid];used.update((edge.source,edge.sink))
    ledger.update(used-unions[q['net_id']]);unions[q['net_id']].update(used)
  assert dict(ledger)=={int(k):v for k,v in initial['ledger'].items()}
 assert len(set(updates))==1,'Require whole nested update bytes, not merely finalpaths'
 chosen=json.loads(updates[0])['incremental'];queries={q['connection_id']:q for q in ep['connections']};assert len(chosen['records'])==len(queries);ledger=Counter();unions=defaultdict(set);parents=defaultdict(dict)
 for record in chosen['records']:
  q=queries[record['connection_id']];assert all(record[key]==value for key,value in q.items());node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;net=q['net_id']
  for eid in record['answer']['physical_edge_ids']:
   edge=a.graph.edges[eid];assert edge.source==node and edge.sink not in used;node=edge.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],edge.switch_id);parent=(edge.source,eid);assert node not in parents[net] or parents[net][node]==parent;parents[net][node]=parent
  assert node==q['sink'] and delay==F(record['answer']['delay'],chosen['scale']);ledger.update(used-unions[net]);unions[net].update(used)
 assert dict(ledger)=={int(k):v for k,v in chosen['ledger'].items()} and all(value<=a.caps[node] for node,value in ledger.items());rows.append(dict(count=n,final_paths=len(queries),stage_queries_checked=query_count,single_update_verified=True,live_rollback_verified=True,stage_wall_seconds=[x['seconds'] for x in row['runs']],complete=True));print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='All3 newplacement targets, one resident run each, independent full demandarrays match everynativequery and finaloriginalXML path/RC/tree/capacity/ledger proof. Actualcases need no historyrepair; repair exercised separately inbitonicinitial trace. Whole nested update bytes equal, producer checks context/metadata/history/owner/other/costarrays/liveledger restoration. Same3 swaps repeated, not acceptedcontinuousmoves/nativeFULLSTA/CPD or fullnetgain.'),indent=2)+'\n')
