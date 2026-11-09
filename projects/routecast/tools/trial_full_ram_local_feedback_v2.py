"""Whole-net frozen feedback pilot with actual search and atomic ledger commit."""
import json,subprocess,time,signal
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from physical_prediction_audit import audit
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_local_feedback_v2_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_ram_length_switch_prediction_v1_2026-10-09';P=E/'full_ram_own_excluded_channel_prediction_v1_2026-10-09'
graph=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml';endpoint=E/'full_ram_comb_constant_endpoints_v1_2026-10-09/cw192.json';binary=R/'build/routecast_net_pressure_v1'
paths=[Path(__file__),graph,endpoint,binary,B/'prediction.json',P/'prediction.json',P/'csr/manifest.json',P/'csr/own_reduction.bin',R/'tools/rr_local_batch_occupancy.py',R/'tools/rr_occupancy.py',R/'tools/physical_prediction_audit.py']
bindings={str(p):sha(p) for p in paths}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,selection='Top20 original overloaded nodes ordered descending excess then raw ID; whole owner nets, all their connections',scope='Frozen original background; selected results must equal already completed full own-excluded search. Retained old paths outside subset mean composition is not full new optimization. Actual initialization/search/atomic commit/audit counted, reused CSR preparation separate.',timeout_s=600),indent=2)+'\n')
def timeout(*args):raise TimeoutError('600s budget')
signal.signal(signal.SIGALRM,timeout);signal.alarm(600);worker=None;start=time.perf_counter();status='FAILED';details={}
try:
 t=time.perf_counter();g=read_rr_graph(graph);e=json.loads(endpoint.read_text());bg=json.loads((B/'prediction.json').read_text());full=json.loads((P/'prediction.json').read_text());assert full['completed']==bg['completed']==16819
 audit(g,e,bg);initial_audit_s=time.perf_counter()-t
 owners=defaultdict(set);own=defaultdict(set);groups=defaultdict(list)
 for c in bg['connections']:
  groups[c['net_id']].append(c);nodes={c['source'],*(g.edges[eid].sink for eid in c['physical_edge_ids'])};own[c['net_id']].update(nodes)
 for net,nodes in own.items():
  for n in nodes:owners[n].add(net)
 overloaded={n:len(nets)-g.nodes[n].capacity for n,nets in owners.items() if len(nets)>g.nodes[n].capacity}
 top=sorted(overloaded,key=lambda n:(-overloaded[n],n))[:20];selected=sorted(set().union(*(owners[n] for n in top)))
 ledger=LocalBatchOccupancy(g);t=time.perf_counter()
 for c in bg['connections']:assert ledger.update(c['connection_id'],1,c['net_id'],c['source'],c['sink'],c['physical_edge_ids'])==Result.COMMITTED
 ledger_init_s=time.perf_counter()-t
 expected={c['connection_id']:c['physical_edge_ids'] for c in full['connections']};updates=[];replacement={};t=time.perf_counter()
 worker=subprocess.Popen([str(binary),str(P/'csr'),'--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
 with (D/'net_results.jsonl').open('x') as journal:
  for net in selected:
   cohort=groups[net];source=cohort[0]['source'];targets=sorted({c['sink'] for c in cohort})
   worker.stdin.write(' '.join(map(str,[source,*targets]))+' | '+' '.join(map(str,sorted(own[net])))+'\n');worker.stdin.flush()
   result=json.loads(worker.stdout.readline());assert not result['budget_exhausted'];journal.write(json.dumps(dict(net_id=net,result=result))+'\n');journal.flush()
   for c in cohort:
    path=result['paths'][str(c['sink'])];assert path==expected[c['connection_id']]
    replacement[c['connection_id']]={**c,'physical_edge_ids':path,'method':'local_frozen_feedback'};updates.append(dict(connection_id=c['connection_id'],epoch=2,net_id=net,source=source,sink=c['sink'],edge_ids=path))
 worker.stdin.close();assert worker.wait()==0;search_s=time.perf_counter()-t;t=time.perf_counter();assert ledger.update_batch(updates)==Result.COMMITTED;commit_s=time.perf_counter()-t
 pred=dict(physical_graph_sha256=g.sha256,connections=[replacement.get(c['connection_id'],c) for c in bg['connections']],node_occupancy={str(n):v for n,v in ledger.occupancy.items() if v},requested=16819,completed=16819)
 pred['methods']=dict(Counter(c['method'] for c in pred['connections']))
 t=time.perf_counter();checked=audit(g,e,pred);audit_s=time.perf_counter()-t;(D/'prediction.json').write_text(json.dumps(pred)+'\n')
 details=dict(top_nodes=top,selected_nets=selected,recomputed_connections=len(updates),initial_audit_and_load_s=initial_audit_s,ledger_init_s=ledger_init_s,actual_search_s=search_s,atomic_commit_s=commit_s,final_audit_s=audit_s,all_selected_paths_equal_full_search=True,audit=checked);status='COMPLETE_AUDITED_LOCAL_FEEDBACK'
except Exception as error:details=dict(error=repr(error))
finally:
 signal.alarm(0)
 if worker is not None and worker.poll() is None:worker.kill();worker.wait()
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(status=status,details=details,bindings=bindings,total_s=time.perf_counter()-start),indent=2)+'\n');print(status,details,flush=True)
