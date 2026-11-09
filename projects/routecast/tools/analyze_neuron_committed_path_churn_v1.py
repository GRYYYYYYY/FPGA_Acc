"""Full certified neuron path churn with resource reservation for live factor1."""
import datetime,json,resource,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from bounded_model_json_stream_v1 import records
from compare_complete_receipt_events_stream_v1 import round_items
from measure_committed_path_churn_v1 import Replay,paths
case=R/'experiments/titan23_neuron_compiled_criticality_pipeline_v1_2026-10-15'
cert=R/'experiments/neuron_compiled_final_admission_v1_2026-10-15/verification.json'
v=json.loads(cert.read_text());assert v['all_pass']
model=R/'experiments/titan23_neuron_scaled_present_factor1_pipeline_v1_2026-10-15';launch=json.loads((model/'launch_observation_v1.json').read_text());p=Path('/proc')/str(launch['model_pid']);a=(p/'stat').read_text().rsplit(')',1)[1].split();assert int(a[19])==launch['model_startticks'] and a[0]!='Z'
vm=int(next(x for x in (p/'status').read_text().splitlines() if x.startswith('VmSize:')).split()[1])*1024;reserve=max(0,20*2**30-vm);free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());limit=512*2**20
admission=dict(shared_headroom_bytes=free,remaining_original_model_reservation_bytes=reserve,child_limit_bytes=limit,margin_bytes=8*2**30,admitted=free>=reserve+limit+8*2**30);assert admission['admitted'],'Analysis not launched: memory admission unavailable'
resource.setrlimit(resource.RLIMIT_AS,(limit,limit));tick=time.perf_counter();bindings={**closure([Path(__file__),R/'tools/test_measure_committed_path_churn_v1.py']),str(cert):sha(cert)}
for name in ['initial.json','receipt.json','sketch.json']:
 p=case/'model'/name;h=sha(p);assert h==v['bindings'][str(p)];bindings[str(p)]=h
replay=Replay(records(case/'model/initial.json'));assert replay.connections==77106 and len(replay.current)==50767
rows=[]
for kind,index,value in round_items(case/'model/receipt.json'):
 if kind=='event':replay.event(index,value)
 else:rows.append(dict(round_index=index,**replay.finish_round(index,value)))
assert len(rows)==2 and all(x['events']==50767 for x in rows)
seen=set()
for rec in records(case/'model/sketch.json'):
 cid=rec['connection_id'];assert cid not in seen;seen.add(cid)
 assert paths([rec])[cid]==replay.current[rec['net_id']][cid]
assert len(seen)==77106
assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),resource_admission=admission,all_original_connections=77106,all_events=101534,final_state_path_signatures_equal=True,rounds=rows,scope='Complete certified baseline accepted path churn; source/sink and ordered physical edge IDs compared against actual previous committed state. Changed rejected candidates are not accepted changes. Repeated primary search calls in unchanged commits are counts, not per-NET settled-work/timing or proof those searches could be skipped. No causal scheduling, quality or end-to-end gain claim.',seconds=time.perf_counter()-tick)
out=R/'experiments/neuron_committed_path_churn_v1_2026-10-15';out.mkdir();(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)
