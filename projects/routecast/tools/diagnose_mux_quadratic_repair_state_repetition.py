"""Replay archived repair records/history, distinguish routing repetition from full state."""
import json,hashlib
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_quadratic_history_online_loop_2026-10-06';out=ROOT/'experiments/mux_quadratic_repair_state_repetition_2026-10-06';out.mkdir(exist_ok=True)
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def paths(records):return [[cid,r['net_id'],r['source'],r['sink'],r['answer']['physical_edge_ids']] for cid,r in sorted(records.items())]
receipt=json.loads((base/'receipt.json').read_text());rows=[];bindings={}
for item in receipt['rows']:
 if item['status']=='PRIOR_ALLOCATION_SKIP':continue
 file=base/f"w{item['width']}_m{item['index']}/result.json";assert sha(file)==item['result_sha256'];bindings[str(file)]=sha(file);data=json.loads(file.read_text())
 for index,attempt in enumerate(data['attempts']):
  update=attempt['update'];initial=update['incremental'];final=update['repair'];assert final
  records={r['connection_id']:r for r in initial['records']};history=Counter({int(k):v for k,v in initial['history'].items()});seen={};releases=[]
  for event_index,event in enumerate(final['events']):
   if event['type']=='QUERY' and event['committed']:
    q=event['query'];assert q['connection_id'] not in records;records[q['connection_id']]={**q,'mode':'NATIVE_HISTORY_DELAY_COST','answer':event['answer']}
   elif event['type']=='RELEASE':
    owners=set(event['blocker_NETs']);removed=sorted(cid for cid,r in records.items() if r['net_id'] in owners);assert removed==event['removed_connection_ids']
    key=(event['failed_query']['connection_id'],tuple(event['blocker_NETs']));routing=digest(paths(records));owner=digest(paths({cid:r for cid,r in records.items() if r['net_id'] in owners}));hist=digest(sorted(history.items()));prior=seen.get(key,[])
    releases.append(dict(event=event_index,failed_connection=key[0],owners=list(key[1]),records=len(records),routing_sha256=routing,owner_paths_sha256=owner,history_sha256=hist,repeated_pair=bool(prior),same_routing_any_prior=any(routing==x[0] for x in prior),same_owner_paths_any_prior=any(owner==x[1] for x in prior),same_routing_and_history_any_prior=any((routing,hist)==(x[0],x[2]) for x in prior)))
    seen.setdefault(key,[]).append((routing,owner,hist))
    for cid in removed:del records[cid]
    history.update(event['frontier']);assert dict(history)=={int(k):v for k,v in event['history_after'].items()}
  assert records=={r['connection_id']:r for r in final['records']};assert dict(history)=={int(k):v for k,v in final['history'].items()};assert len(releases)==final['repairs']
  rows.append(dict(case=file.parent.name,attempt=index,releases=releases,final_records_verified=True,final_history_verified=True))
totals={key:sum(r[key] for row in rows for r in row['releases']) for key in ['repeated_pair','same_routing_any_prior','same_owner_paths_any_prior','same_routing_and_history_any_prior']}
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),input_receipt_sha256=sha(base/'receipt.json'),bindings=bindings,rows=rows,totals=totals,scope='Available receipt snapshot only; exact replay of committed connection records and history through all repair events, with final equality. Signatures cover physical paths, not full native search state/pending queue. Same routing and history is necessary but insufficient for full-state cycle; changing history does not ensure progress.'),indent=2)+'\n');print(totals)
