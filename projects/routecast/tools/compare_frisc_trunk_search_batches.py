"""Authenticate complete full/target search equivalence on the fixed cohort."""
import json
from pathlib import Path
from pre_route_endpoints import sha
out=Path('experiments/frisc_trunk_search_batch_comparison_2026-10-05')
if out.exists():raise ValueError('fresh output required')
roots=[Path('experiments/frisc_shared_trunk_batch_2026-10-05'),Path('experiments/frisc_shared_trunk_target_batch_2026-10-05')];loaded=[];inputs={}
for root in roots:
 receipt=json.loads((root/'receipt.json').read_text());protocol=json.loads((root/'protocol.json').read_text());assert sha(root/'protocol.json')==receipt['protocol_sha256'] and sha(root/'prediction.json')==receipt['prediction_sha256'] and sha(root/'attempted_paths.json')==receipt['attempted_paths_sha256'] and sha(root/'source.py')==receipt['source_sha256'] and sha(root/'search.py')==receipt['search_sha256'];assert all(sha(p)==h for p,h in receipt['input_sha256'].items());loaded.append((receipt,protocol,json.loads((root/'prediction.json').read_text()),json.loads((root/'attempted_paths.json').read_text())))
 for name in ('receipt.json','protocol.json','prediction.json','attempted_paths.json','source.py','search.py'):inputs[str(root/name)]=sha(root/name)
a,b=loaded;assert a[0]['input_sha256']==b[0]['input_sha256'];assert a[1]['net_ids']==b[1]['net_ids'] and a[1]['requests']==b[1]['requests'] and a[1]['policy']==b[1]['policy'];assert a[2]==b[2] and a[3]==b[3]
keys=('net','requested','built','failure','committed','before_scores','candidate_scores');decisions=[]
for x,y in zip(a[0]['reports'],b[0]['reports']):
 assert {k:x.get(k) for k in keys}=={k:y.get(k) for k in keys};assert [{k:v for k,v in q.items() if k!='query_s'} for q in x['queries']]==[{k:v for k,v in q.items() if k!='query_s'} for q in y['queries']];decisions.append({k:x.get(k) for k in keys})
assert len(a[0]['reports'])==len(b[0]['reports'])==len(a[1]['net_ids']);counts=[sum(len(x['queries']) for x in r[0]['reports']) for r in loaded];assert counts[0]==counts[1]
costs=[{'full_wall_s':r[0]['full_wall_s'],'query_wall_sum_s':sum(q['query_s'] for x in r[0]['reports'] for q in x['queries'])} for r in loaded];out.mkdir();(out/'source.py').write_text(Path(__file__).read_text());result={'cohort_net_count':len(decisions),'attempted_query_count':counts[0],'all_attempted_paths_exact':True,'final_prediction_exact':True,'all_query_outcomes_and_net_decisions_exact':True,'decisions':decisions,'observed_stage_costs':{'full':costs[0],'target':costs[1]},'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'scope':'whole fixed-cohort CPU optimization equivalence; concurrent host wall costs descriptive, includes cohort preparation/commit/audit but excludes prior library/frontend/native STA; no unseen-family or end-to-end/hardware speed claim'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','decisions')}))
