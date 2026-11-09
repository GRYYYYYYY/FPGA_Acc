"""Frozen full-state placement feedback; affected whole nets, fixed length costs."""
import json,subprocess,time,signal,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
from feedback_scores import scores
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_swap_persistent_feedback_v1_2026-10-09';D.mkdir(exist_ok=False)
C=E/'full_ram_swap_candidates_v1_2026-10-09';B=E/'full_ram_length_switch_prediction_v1_2026-10-09';base=E/'full_ram_comb_only_route_v1_2026-10-09';endpoint=E/'full_ram_comb_constant_endpoints_v1_2026-10-09/cw192.json';binary=R/'build/full_ram_preflight_matched_v1_2026-10-09/B'
provenance=R/'build/full_ram_preflight_matched_v1_2026-10-09/provenance.json'
for p,h in json.loads(provenance.read_text())['bindings'].items():assert sha(p)==h
r=json.loads((C/'receipt.json').read_text());br=json.loads((B/'receipt.json').read_text());assert br['status']=='COMPLETE_AUDITED_PREDICTION'
for p,h in {**r['bindings'],**br['bindings'],**br['files']}.items():assert sha(p)==h
paths=[E/'full_ram_swap_incremental_v1_2026-10-09/receipt.json',*[E/f'full_ram_swap_incremental_v1_2026-10-09/candidate_{i}/prediction.json' for i in (1,2)],provenance,R/'tools/csr_consumer/validated_once_main_v1.cpp',R/'tools/csr_consumer/validated_once_search_v1.hpp',Path(__file__),C/'receipt.json',B/'receipt.json',endpoint,binary,R/'tools/feedback_scores.py',R/'tools/physical_prediction_audit.py',R/'tools/rr_local_batch_occupancy.py',R/'tools/rr_occupancy.py']
for row in r['results']:
 folder=C/('candidate_'+str(row['candidate']));assert sha(folder/'design.place')==row['place_sha256'];assert sha(folder/'endpoints.json')==row['endpoint_sha256'];paths.extend([folder/'design.place',folder/'endpoints.json'])
bindings={str(p):sha(p) for p in paths}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,rule='Minimize predicted unique-net channel span, then channel excess, then candidate ID; include baseline0; evaluate both frozen candidates',cost='Fixed original length-switch CSR; affected whole nets from prospective endpoint differences; no pressure or native route input',timeout_s=600,scope='Fresh full feedback stage with one O2 immutable-consumer session and one initialized background ledger, full per-candidate fork counted; candidates both based on original state. Not a matched single-factor ablation. Development Full placement feedback correctness and measured incremental stages; unmodified nets fixed-cost independent search context preserved. Original baseline acquisition and candidate extraction costs separately counted, not free.'),indent=2)+'\n')
def positions(path,names):
 out={}
 for line in path.read_text().splitlines():
  w=line.split()
  if len(w)>=6 and w[0] in names:assert w[0] not in out;out[w[0]]=tuple(map(int,w[1:5]))
 assert set(out)==set(names) and len(set(out.values()))==len(out);return out
signal.signal(signal.SIGALRM,lambda *args:(_ for _ in ()).throw(TimeoutError('600s budget')));signal.alarm(600);worker=None;start=time.perf_counter();status='FAILED';details={}
try:
 t=time.perf_counter();g=read_rr_graph(base/'rr_graph.xml');ep0=json.loads(endpoint.read_text());bg=json.loads((B/'prediction.json').read_text());audit(g,ep0,bg)
 types={b.get('name'):b.get('instance').split('[')[0] for b in ET.parse(base/'design.net').getroot().findall('block')};pos0=positions(base/'design.place',types)
 old={c['connection_id']:c for c in ep0['connections']};background={c['connection_id']:c for c in bg['connections']};load_s=time.perf_counter()-t
 t=time.perf_counter();ledger0=LocalBatchOccupancy(g)
 for c in bg['connections']:assert ledger0.update(c['connection_id'],1,c['net_id'],c['source'],c['sink'],c['physical_edge_ids'])==Result.COMMITTED
 shared_ledger_init_s=time.perf_counter()-t
 worker=subprocess.Popen([str(binary),str(B/'csr'),'--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
 reports=[dict(candidate=0,scores=scores(g,ep0,bg['node_occupancy']))]
 for row in r['results']:
  cid=row['candidate'];folder=C/f'candidate_{cid}';out=D/f'candidate_{cid}';out.mkdir();ep=json.loads((folder/'endpoints.json').read_text());pos=positions(folder/'design.place',types);a,b=row['swapped']
  assert types[a]==types[b]=='clb' and pos[a]==pos0[b] and pos[b]==pos0[a] and all(pos[n]==pos0[n] for n in types if n not in (a,b))
  assert len(ep['connections'])==len(old)==16819 and {c['connection_id'] for c in ep['connections']}==set(old)
  changed=[];groups=defaultdict(list)
  for c in ep['connections']:
   prior=old[c['connection_id']];assert prior['net_id']==c['net_id'];groups[c['net_id']].append(c)
   if (c['source'],c['sink'])!=(prior['source'],prior['sink']):changed.append(c['connection_id'])
  assert sorted(changed)==sorted(row['affected_connections']);selected={old[i]['net_id'] for i in changed}
  t=time.perf_counter();ledger=ledger0.fork()
  init_s=time.perf_counter()-t;t=time.perf_counter();replacement={};updates=[];visits=0
  with (out/'net_results.jsonl').open('x') as journal:
   for net in sorted(selected):
    cohort=groups[net];source=cohort[0]['source'];assert all(c['source']==source for c in cohort)
    worker.stdin.write(' '.join(map(str,[source,*sorted({c['sink'] for c in cohort})]))+'\n');worker.stdin.flush();result=json.loads(worker.stdout.readline());assert not result['budget_exhausted'];visits+=result['edge_visits'];journal.write(json.dumps(dict(net_id=net,result=result))+'\n')
    for c in cohort:
     path=result['paths'][str(c['sink'])];replacement[c['connection_id']]={**c,'physical_edge_ids':path,'method':'swap_incremental'};updates.append(dict(connection_id=c['connection_id'],epoch=2,net_id=net,source=source,sink=c['sink'],edge_ids=path))
  search_s=time.perf_counter()-t;t=time.perf_counter();assert ledger.update_batch(updates)==Result.COMMITTED;commit_s=time.perf_counter()-t
  rows=[replacement.get(c['connection_id'],background[c['connection_id']]) for c in ep['connections']];pred=dict(physical_graph_sha256=g.sha256,connections=rows,node_occupancy={str(n):v for n,v in ledger.occupancy.items() if v},requested=16819,completed=16819,methods=dict(Counter(c['method'] for c in rows)))
  t=time.perf_counter();checked=audit(g,ep,pred);audit_s=time.perf_counter()-t;(out/'prediction.json').write_text(json.dumps(pred)+'\n');report=dict(candidate=cid,changed_endpoints=len(changed),affected_nets=len(selected),recomputed_connections=len(updates),full_ledger_fork_s=init_s,search_s=search_s,commit_s=commit_s,audit_s=audit_s,edge_visits=visits,scores=scores(g,ep,pred['node_occupancy']),audit=checked);reports.append(report);print(report,flush=True)
 selected=min(reports,key=lambda x:(x['scores']['channel_net_span_sum'],x['scores']['predicted_channel_overuse_units'],x['candidate']))['candidate']
 worker.stdin.close();assert worker.wait()==0
 details=dict(shared_ledger_init_s=shared_ledger_init_s,load_and_initial_audit_s=load_s,reports=reports,selected_candidate=selected);reference=json.loads((E/'full_ram_swap_incremental_v1_2026-10-09/receipt.json').read_text());assert selected==reference['details']['selected_candidate']
 for item in reports:assert item['scores']==reference['details']['reports'][item['candidate']]['scores']
 for candidate in (1,2):
  expected=json.loads((E/f'full_ram_swap_incremental_v1_2026-10-09/candidate_{candidate}/prediction.json').read_text());actual=json.loads((D/f'candidate_{candidate}/prediction.json').read_text());assert actual==expected
 details['all_complete_candidate_predictions_equal_reference']=True
 status='COMPLETE_AUDITED_INCREMENTAL_DECISION'
except Exception as error:details=dict(error=repr(error))
finally:
 signal.alarm(0)
 if worker is not None and worker.poll() is None:worker.kill();worker.wait()
assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(status=status,details=details,bindings=bindings,total_s=time.perf_counter()-start),indent=2)+'\n');print(status,details,flush=True)
