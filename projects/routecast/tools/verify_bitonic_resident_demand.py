"""Independent full-map native demand digest replay, not caller dirty replay."""
import json,hashlib
from array import array
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_resident_demand_2026-10-07';old=ROOT/'experiments/bitonic_owned_four_repair_prediction_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());prior=json.loads((old/'verification.json').read_text());assert prior['receipt_sha256']==sha(old/'receipt.json');assert r['complete'] and r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items()) and all(sha(f)==h for f,h in p['inputs'].items());rows=[]
for row in r['rows']:
 n=row['count']
 for name,key in [(f'n{n}.json','candidate_sha256'),(f'n{n}_initial.json','initial_sha256')]:assert (out/name).read_bytes()==(old/name).read_bytes() and sha(out/name)==row[key]
 initial=json.loads((out/f'n{n}_initial.json').read_text());c=json.loads((out/f'n{n}.json').read_text());epfile=next(Path(f) for f in p['inputs'] if Path(f).parent.name==f'n{n}');ep=json.loads(epfile.read_text());graph=ImmutableXMLAudit(Path(ep['inputs']['graph']['path']),ep['graph_sha256']);journal=json.loads((out/f'n{n}_demand_journal.json').read_text());unions=defaultdict(set);records={};ledger=Counter();index=0;last_epoch=0
 def check(q,answer,committed,mode):
  global_dummy=None
  nonlocal_dummy=None
  entry=journal[index];assert (entry['source'],entry['sink'],entry['mode'])==(q['source'],q['sink'],mode);assert entry['epoch']>last_epoch
  # Construct full expected map at every query, without reading dirty updates.
  full=array('Q',[0])*len(graph.caps)
  if mode=='resident':
   owner=unions[q['net_id']]
   for node,value in ledger.items():full[node]=value-int(node in owner)
  assert hashlib.sha256(full.tobytes()).hexdigest()==entry['digest']
  if committed:
   assert q['connection_id'] not in records;used={q['source']}
   for eid in answer['physical_edge_ids']:
    edge=graph.graph.edges[eid];used.update((edge.source,edge.sink))
   ledger.update(used-unions[q['net_id']]);unions[q['net_id']].update(used);records[q['connection_id']]=q
 for k,event in enumerate(initial['attempts']):
  check(event['query'],event['native_answer'],k<len(initial['records']),'resident');last_epoch=journal[index]['epoch'];index+=1
 assert dict(ledger)=={int(k):v for k,v in initial['ledger'].items()}
 for event in c.get('events',[]):
  if event['type'] in ('QUERY','BUDGET_WITNESS'):
   mode='full' if event['type']=='BUDGET_WITNESS' else 'resident';check(event['query'],event['answer'],event.get('committed',False),mode);last_epoch=journal[index]['epoch'];index+=1
  elif event['type']=='RELEASE':
   assert event['removed_connection_ids']==sorted(cid for cid,q in records.items() if q['net_id'] in event['blocker_NETs'])
   for net in event['blocker_NETs']:assert sorted(unions[net])==event['released_unions'][str(net)];ledger.subtract(unions[net]);del unions[net]
   ledger+=Counter()
   for cid in event['removed_connection_ids']:del records[cid]
  else:raise AssertionError('unknown event')
 assert index==len(journal);assert dict(ledger)=={int(k):v for k,v in c['ledger'].items()};stats=json.loads((out/f'n{n}_profile.json').read_text());assert stats['phases']['native_query']['calls']==index and stats['phases']['query_total']['calls']==sum(x['mode']=='full' for x in journal);assert stats['resident_demand']['calls']==sum(x['mode']=='resident' for x in journal)
 rows.append(dict(count=n,query_demand_digests_checked=index,final_connections=len(records),phase_stats=stats,initial_search_seconds=row['search_seconds'],repair_seconds=row['repair_seconds'],journal_sha256=sha(out/f'n{n}_demand_journal.json'),profile_sha256=sha(out/f'n{n}_profile.json'),candidate_sha256=row['candidate_sha256']));print(n,index,'full demand digests match native snapshots',flush=True)
contract=ROOT/'experiments/capacity_local_demand_contract_2026-10-07/verification.json';cv=json.loads(contract.read_text());assert cv['implementation_sha256']==sha(ROOT/'tools/capacity_local_demand.py');assert [x['count'] for x in rows]==[4,8,16];(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),prior_verification_sha256=sha(old/'verification.json'),contract_sha256=sha(contract),rows=rows,scope='All3 initial/final bytes identical oldindependentlyaudited candidates. EVERY actualnativequery resident/witness demand digest equals independently reconstructed FULL demand array from committed/released NET unions; no reliance on callerdirtyset. Release and externalrelaxedquery resync covered. Query clocks changed: query_total onlyfullwitness; native_query ALL. Separateinstrumentedobservations not stablepaired/fullgain. Serialcaller contract requires complete dirties; staleepoch not missingdirty detector.'),indent=2)+'\n')
