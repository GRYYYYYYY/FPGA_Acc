"""Complete per-request work invariants and byte equality in same-binary replay."""
import json,sys
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
D=Path(sys.argv[1]).resolve();P=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else None;proof=json.loads((D/'verification.json').read_text());assert proof['all_cases_both_complete_arms_authenticated'] and all(sha(p)==h for p,h in proof['bindings'].items());N=D/'seed/native/sha1';sr=json.loads((N/'service_receipt.json').read_text());assert all(sha(p)==h for section in ['bindings','files'] for p,h in sr[section].items());calls=sr['calls'];names=['phase','net','kind','targets','reset','discovered','scans','pops','stale','settled','relax','pushes','refills','moves','tops'];work=N/'work.tsv';lines=work.read_text().splitlines();assert len(lines)==len(calls)==7459;rows=[];totals=defaultdict(lambda:defaultdict(int))
for line,call in zip(lines,calls):
 x=line.split();assert len(x)==16 and x[0]=='W';row={name:(v if name=='kind' else int(v)) for name,v in zip(names,x[1:])};assert row['phase']==call['phase'] and row['net']==call['native_net'] and row['kind'] in {'F','B'};assert row['targets']==1 if row['kind']=='B' else row['targets']>=2
 assert row['pops']==row['settled']+row['stale'] and row['pops']<=row['pushes'];assert row['pushes']==row['relax']+(2 if row['kind']=='B' else 1);assert row['settled']<=row['discovered']<=91088*(2 if row['kind']=='B' else 1);assert row['reset']<=182176 and row['moves']>=row['refills']
 for k in names[3:]:totals[row['kind']][k]+=row[k]
 totals[row['kind']]['calls']+=1;rows.append(row)
assert totals['F']['calls']==2366 and totals['B']['calls']==5093
files=[Path(__file__).resolve(),D/'verification.json',N/'service_receipt.json',work];replays=[]
if P:
 p=P/'receipt.json';v=json.loads(p.read_text());assert v['all2_complete_corpus_replays_pass'] and all(sha(q)==h for q,h in v['bindings'].items());files.append(p)
 for r in v['rows']:
  w=P/f"{r['index']}_{r['variant']}"/'work.tsv';assert w.read_bytes()==work.read_bytes();assert r['matched_receive_lines']==24640 and r['all_response_lines_and_native_route_bytes_equal'];files.append(w);replays.append(dict(index=r['index'],all7459_request_reset_discovery_scan_heap_counts_byte_identical=True))
(D/'work_verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in files},all7459_per_request_work_count_invariants_pass=True,totals=dict(totals),replays=replays,scope='Full work counters, no sampled request: same request IDs/order, edges/pops/stale/settled/relax/heaprefills/moves/tops and reset/discovered counts. Equal counts do not independently prove identical visited-node sets, cache events, instruction cycles or frequency.'),indent=2)+'\n');print(json.dumps(dict(totals=dict(totals),replays=replays),indent=2))
