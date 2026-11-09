"""All24 native logs: iteration totals, counted routing attempts and phase clocks."""
import json,re
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'declared_mux_native_work_v1_2026-10-08';D.mkdir(exist_ok=False)
vp=E/'declared_mux_session_comparison_v1_2026-10-08/verification.json';verified=json.loads(vp.read_text());assert all(sha(f)==h for f,h in verified['bindings'].items())
source=R/'build/native_resume_branch_partial_v8_2026-10-08/source/route.cpp';bp=source.parents[1]/'protocol.json';br=source.parents[1]/'receipt.json';buildp=json.loads(bp.read_text());buildr=json.loads(br.read_text());assert sha(bp)==buildr['protocol_sha256'] and sha(source)==buildp['sources'][str(source)]
bindings={str(vp):sha(vp),str(source):sha(source),str(bp):sha(bp),str(br):sha(br),str(Path(__file__)):sha(Path(__file__))}
seedreceipt=E/'retained_seed_session_cohort_v2_2026-10-08/receipt.json';sr=json.loads(seedreceipt.read_text());bindings[str(seedreceipt)]=sha(seedreceipt)
iteration=re.compile(r'^\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\(',re.M)
def extract(path):
 bindings[str(path)]=sha(path);text=path.read_text()
 totals=re.findall(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',text);assert len(totals)==1
 nets,connections,pushes,pops=map(int,totals[0]);n=int(re.findall(r'Successfully routed after (\d+) routing iterations\.',text)[0])
 rows=[dict(iteration=int(x[0]),printed_iteration_seconds=x[1],heap_pushes=int(x[4]),nets_routed=int(x[5]),connections_routed=int(x[6]),overused_nodes=int(x[7])) for x in iteration.findall(text)]
 assert [x['iteration'] for x in rows]==list(range(1,n+1))
 assert sum(x['heap_pushes'] for x in rows)==pushes and sum(x['nets_routed'] for x in rows)==nets and sum(x['connections_routed'] for x in rows)==connections
 pathclock=re.findall(r'Time spent on path search: ([0-9.]+) seconds\.',text);routingclock=re.findall(r'# Routing took ([0-9.]+) seconds',text);lookahead=re.findall(r'# Computing router lookahead map took ([0-9.]+) seconds',text)
 assert len(pathclock)==len(routingclock)==len(lookahead)==1
 return dict(iterations=n,nets_routed_attempts=nets,connection_routing_attempts=connections,heap_pushes=pushes,heap_pops=pops,path_search_seconds_printed=pathclock[0],routing_seconds_printed=routingclock[0],lookahead_seconds_printed=lookahead[0],iteration_rows=rows)
rows=[]
for quality in verified['rows']:
 w,i=quality['width'],quality['index'];seed=extract(E/f'retained_seed_session_native_cohort_v2_2026-10-08/w{w}_m{i}/run.log');cold=extract(E/f'declared_mux_cold_native_cohort_v1_2026-10-08/w{w}_m{i}/run.log');seedrow=next(x for x in sr['rows'] if x['width']==w and x['index']==i)
 rows.append(dict(width=w,index=i,retained_connections=seedrow['retained'],released_connections=seedrow['released'],seed=seed,cold=cold,connection_attempt_ratio=str(F(seed['connection_routing_attempts'],cold['connection_routing_attempts'])),heap_push_ratio=str(F(seed['heap_pushes'],cold['heap_pushes'])),printed_joint_nonregression=quality['printed_joint_nonregression']))
assert len(rows)==12 and all(sha(f)==h for f,h in bindings.items())
report=dict(bindings=bindings,rows=rows,cases_fewer_connection_attempts=sum(x['seed']['connection_routing_attempts']<x['cold']['connection_routing_attempts'] for x in rows),cases_fewer_heap_pushes=sum(x['seed']['heap_pushes']<x['cold']['heap_pushes'] for x in rows),seed_total_connection_attempts=sum(x['seed']['connection_routing_attempts'] for x in rows),cold_total_connection_attempts=sum(x['cold']['connection_routing_attempts'] for x in rows),seed_total_heap_pushes=sum(x['seed']['heap_pushes'] for x in rows),cold_total_heap_pushes=sum(x['cold']['heap_pushes'] for x in rows),scope='Full12 developer cases, all iteration rows summed to native Router Stats counters. Attempts repeat connections/nets across routing iterations, not distinct demands, not number of missing branches. Printed phase clocks rounded and cannot resolve small differences or be summed into an exact workflow. Source-bound counter names; no changed budget/native algorithm, causal paired runtime gain or unseen-family claim.')
(D/'diagnosis.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k not in ('bindings','rows')})
