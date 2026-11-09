"""Frozen wholeNET incremental reroute after genuine placement swap."""
import copy,json,time
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_swap_incremental_2026-10-06';out.mkdir();swap=root/'experiments/ex5p_placement_swap_2026-10-06';m=json.loads((swap/'receipt.json').read_text());assert sha(swap/'endpoints.json')==m['endpoint_sha256'];priorpath=root/'experiments/ex5p_shared_ledger_engine_2026-10-06/3/receipt.json';prior=json.loads(priorpath.read_text());proof=json.loads((priorpath.parent/'verification.json').read_text());assert proof['receipt_sha256']==sha(priorpath);new=json.loads((swap/'endpoints.json').read_text());affected=set(m['affected_net_ids']);p={'prior_sha256':sha(priorpath),'moved_endpoint_sha256':sha(swap/'endpoints.json'),'swap_receipt_sha256':sha(swap/'receipt.json'),'policy':'Stage whole affectedNET release; query all moved affectedNET connections in NET/connection order, hardcapacity/exactdelayhistory/original1ns/10000labels; stop first failure/conflict, no further repair. Candidate only, live prior untouched. No native route/timing reads.','affected_nets':sorted(affected)};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
start=time.monotonic();ctx=PersistentRCContext(swap/'endpoints.json');ctx.set_history({int(n):c for n,c in prior['history'].items()});f=ctx.rc.fields;slots={f['edge_ids'][s]:(u,f['dest_ranks'][s]) for u in range(ctx.native.n) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};records={r['connection_id']:copy.deepcopy(r) for r in prior['records'] if r['net_id'] not in affected};unions=defaultdict(set);parents=defaultdict(dict)
for r in records.values():
 net=r['net_id'];unions[net].add(r['source'])
 for eid in r['answer']['physical_edge_ids']:u,n=slots[eid];unions[net].add(n);parents[net][n]=(u,eid)
ledger=Counter(n for ns in unions.values() for n in ns);setup=time.monotonic()-start;events=[];failure=None;start=time.monotonic()
for q in sorted((q for q in new['connections'] if q['net_id'] in affected),key=lambda q:(q['net_id'],q['connection_id'])):
 net=q['net_id'];other={n:c-int(n in unions[net]) for n,c in ledger.items()};a=ctx.query(q['source'],q['sink'],ctx.rc.scale//10**9,{n:c for n,c in other.items() if c});event={'query':q,'answer':a,'committed':False};events.append(event)
 if a['status']!='FOUND':failure={'query':q,'status':a['status']};break
 node=q['source'];used={node};incoming={}
 for eid in a['physical_edge_ids']:u,n=slots[eid];assert u==node;node=n;used.add(n);incoming[n]=(u,eid)
 assert node==q['sink']
 if any(n in parents[net] and parents[net][n]!=value for n,value in incoming.items()):failure={'query':q,'status':'MULTI_PARENT_REJECTED'};break
 parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);records[q['connection_id']]={**q,'mode':'INCREMENTAL_HISTORY_DELAY','answer':a};event['committed']=True
elapsed=time.monotonic()-start
assert sha(priorpath)==p['prior_sha256'];r={'status':'COMPLETE_CANDIDATE' if failure is None else 'INCOMPLETE_NOT_PUBLISHABLE','failure':failure,'events':events,'records':[records[k] for k in sorted(records)],'ledger':dict(ledger),'history':prior['history'],'scale':ctx.rc.scale,'graph_sha256':ctx.context[1],'completed_connections':len(records),'required_connections':len(new['connections']),'context_and_retained_setup_s':setup,'incremental_query_s':elapsed,'live_prior_unchanged':True,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'],len(records),'/',r['required_connections'],'attempts',len(events),'failure',failure)
