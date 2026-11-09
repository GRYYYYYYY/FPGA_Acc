"""Complete current work counters and overlapping native/client clocks."""
from pathlib import Path
from collections import defaultdict
import json,re,math
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10';N=O/'native';proof=json.loads((O/'verification.json').read_text());assert proof['complete_current_MMC_initial_floors_paths_epochs_prices_ledgers_events_and_seed_native_pass'];bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(O/'verification.json'):sha(O/'verification.json')}
s=json.loads((N/'service_receipt.json').read_text());assert all(sha(p)==h for p,h in s['files'].items());fields=['reset','discovered','scans','pops','stale','settled','relax','pushes','refills','moves','tops'];groups=defaultdict(lambda:dict(calls=0,**{k:0 for k in fields}));rows=[];calls=[]
for l in (N/'work.tsv').read_text().splitlines():
 x=l.split('\t');assert len(x)==16 and x[0]=='W';phase,net=int(x[1]),int(x[2]);kind=x[3];target=int(x[4]);values=list(map(int,x[5:]));assert kind in ['F','B'] and target>=1;g=groups[phase,kind];g['calls']+=1
 for key,value in zip(fields,values):g[key]+=value
 calls.append((phase,net));rows.append(dict(phase=phase,native_net=net,kind=kind,targets=target,scans=values[2]))
assert calls==[(r['phase'],r['native_net']) for r in s['calls']] and len(rows)==143776
text=(N/'native.log').read_text();profiles=[]
for m in re.finditer(r'ROUTECAST_PROFILE phase=(\d+) bidi=(\d+) forward=(\d+) kernel=([0-9.]+) answer=([0-9.]+) prices=([0-9.]+) wait=([0-9.]+)',text):
 phase=int(m[1]);assert int(m[2])==groups[phase,'B']['calls'] and int(m[3])==groups[phase,'F']['calls'];client=s['client_search_profile'][phase];assert client['calls']==int(m[2])+int(m[3]);assert float(m[5])>=float(m[4]);profiles.append(dict(phase=phase,kernel_wall=float(m[4]),answer_inclusive=float(m[5]),price_wall=float(m[6]),command_wait_wall=float(m[7]),client=client))
assert len(profiles)==3;cpu=[]
for m in re.finditer(r'ROUTECAST_CPU phase=(\d+) bidi_wall=([0-9.]+) bidi_cpu=([0-9.]+) forward_wall=([0-9.]+) forward_cpu=([0-9.]+)',text):
 phase=int(m[1]);bw,bc,fw,fc=map(float,m.group(2,3,4,5));assert abs(bw+fw-profiles[phase]['kernel_wall'])<1e-6 and bc<=bw+.01 and fc<=fw+.01;cpu.append(dict(phase=phase,bidi_wall=bw,bidi_cpu=bc,forward_wall=fw,forward_cpu=fc))
assert len(cpu)==3;heavy=sorted(rows,key=lambda r:r['scans'],reverse=True)[:math.ceil(len(rows)/100)];total=sum(r['scans'] for r in rows);nativewall=sum(r['kernel_wall'] for r in profiles);nativecpu=sum(r['bidi_cpu']+r['forward_cpu'] for r in cpu)
for p in [N/'service_receipt.json',N/'native.log',N/'work.tsv']:bindings[str(p)]=sha(p)
result=dict(bindings=bindings,all143776_work_rows_match_actual_requests=True,work_by_phase_kind=[dict(phase=p,kind=k,**g) for (p,k),g in sorted(groups.items())],native_client_profiles=profiles,cpu_profiles=cpu,total_scans=total,top_one_percent_calls=len(heavy),top_one_percent_scan_fraction=sum(r['scans'] for r in heavy)/total,heaviest_requests=heavy[:20],native_kernel_wall=nativewall,native_kernel_cpu=nativecpu,scope='All current search counters/request order; overlapping client/native/command-wait clocks retained separately. Thread CPU near wall does not attribute host/cache/cgroup causes. No summing timers or speedup claim.')
(O/'search_cost_analysis.json').write_text(json.dumps(result,indent=2)+'\n');print({k:result[k] for k in ['total_scans','top_one_percent_scan_fraction','native_kernel_wall','native_kernel_cpu']})
