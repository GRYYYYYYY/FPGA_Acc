"""Full wire scope and freshly produced price/path/transaction linkage."""
import json,sys
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
D=Path(sys.argv[1]).resolve();M=D/'seed/model/sha1';N=D/'seed/handoff/sha1/live_native';receipt=json.loads((M/'receipt.json').read_text());nr=json.loads((N/'receipt.json').read_text());assert all(sha(p)==h for p,h in receipt['bindings'].items()) and all(sha(p)==h for p,h in nr['bindings'].items())
initial=json.loads((M/'initial.json').read_text());groups=defaultdict(list)
for q in initial['records']:groups[q['net_id']].append(q)
manifest=Path(next(p for p in nr['bindings'] if p.endswith('/queries.txt')));cidnet={}
for line in manifest.read_text().splitlines():
 x=line.split()
 if x[0]=='Q':cidnet[int(x[1])]=int(x[2])
wire=[json.loads(l) for l in (N/'wire.jsonl').read_text().splitlines()];cursor=0

def take(direction):
 global cursor
 row=wire[cursor];cursor+=1;assert set(row)=={direction};return row[direction]
assert take('receive')==f'READY\t{len(groups)}\t6273';calls=[];connections=0
for phase in range(3):
 text=take('send').splitlines();header=text[0].split();assert header[0]=='P';count,weight=map(int,header[1:]);prices={int(a):int(b) for a,b in (l.split() for l in text[1:])};assert len(prices)==count==len(text)-1 and weight==(0 if phase==0 else 50000000)
 expected={} if phase==0 else {int(n):v for n,v in json.loads((M/f'round{phase-1}.json').read_text())['prices'].items()};assert prices==expected;assert take('receive')==f'A\t{phase}'
 events={} if phase==0 else {e['net_id']:e for e in receipt['rounds'][phase-1]['events']};nets=sorted(groups) if phase==0 else receipt['rounds'][phase-1]['affected_nets'];assert set(events)==set(nets) if phase else True
 for net in nets:
  qs=groups[net];nativeids={cidnet[q['connection_id']] for q in qs};assert len(nativeids)==1;native=next(iter(nativeids));assert take('send')==f'S {native}\n';observed={}
  for q in qs:
   x=take('receive').split();assert x[0]=='Q';cid,delay,count=map(int,x[1:4]);path=list(map(int,x[4:]));assert count==len(path) and cid not in observed;observed[cid]=(delay,path)
  assert set(observed)=={q['connection_id'] for q in qs} and take('receive')==f'Z\t{native}\t{len(qs)}'
  if phase==0:records=qs
  else:
   event=events[net]
   if 'primary_attempts' in event:
    for q in event['primary_attempts']:assert observed[q['connection_id']][1]==q['physical_edge_ids']
    records=None
   else:records=event.get('records',event.get('rejected_records'));assert records is not None
  if records is not None:
   for q in records:assert observed[q['connection_id']]==(q['answer']['delay'],q['answer']['physical_edge_ids'])
  calls.append(dict(phase=phase,native_net=native,connections=len(qs)));connections+=len(qs)
assert take('send')=='O\n' and take('receive')==f'DONE\t{connections}' and cursor==len(wire) and calls==nr['calls'];assert len(calls)==7459
ep=json.loads((D/'seed/demand/sha1/endpoints.json').read_text());assert ep['inputs']['graph']['path'] in nr['bindings'] and ep['inputs']['graph']['sha256']==nr['bindings'][ep['inputs']['graph']['path']];assert manifest==N/'queries.txt';
for name in ['design.blif','design.net','design.place']:assert (N/name).read_bytes()==(D/'seed/rr/sha1'/name).read_bytes()
proof=json.loads((M/'shared_audit_receipt.json').read_text());assert proof['all_three_complete_audits_pass'] and all(sha(p)==h for p,h in proof['bindings'].items())
(D/'wire_transaction_verification.json').write_text(json.dumps(dict(all_three_fresh_price_vectors_equal_model=True,all7459_native_NET_requests_match_complete_affected_schedules=True,all_response_paths_link_to_initial_or_primary_or_candidate_transactions=True,connections_returned=connections,bindings={str(p):sha(p) for p in [Path(__file__).resolve(),M/'receipt.json',M/'initial.json',M/'round0.json',M/'round1.json',M/'shared_audit_receipt.json',N/'receipt.json',N/'wire.jsonl',manifest]},scope='Full fresh wire-price/path-to-transaction linkage, no archived prediction consumed. Separate XML audits certify all physical paths and fallback/rejected/epoch/ledger states. Estimate transactions remain owned by Python.'),indent=2)+'\n');print('FULL LIVE WIRE',len(calls),connections)
