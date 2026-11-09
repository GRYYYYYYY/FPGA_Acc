"""Post-hoc aggregate trajectory diagnosis; never selects/tunes routing seeds."""
import json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/freecores_native_trajectory_diagnosis_v1_2026-10-08';D.mkdir()
C=R/'experiments/freecores_continuous_workflow_v1_2026-10-08';proof=C/'verification.json';v=json.loads(proof.read_text());assert v['all_cases_both_complete_arms_authenticated'] and all(sha(k)==h for k,h in v['bindings'].items())
source=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route'
bindings={str(x):sha(x) for x in [Path(__file__),proof,source/'route_utils.cpp',source/'route_net.tpp',source/'router_stats.h',R/'build/native_candidate_retained_search_2026-10-06/source/route.cpp']}
pattern=re.compile(r'^\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\(\s*([\d.]+)%\)\s+(\d+)\s+\(\s*([\d.]+)%\)\s+([\d.]+)\s+(.+)$')
keys=['iteration','rounded_iteration_seconds','rounded_pres_fac','bb_updates','heap_pushes','nets_routed','connections_routed','overused_node_count','rounded_overused_percent','wirelength','rounded_wire_percent','rounded_diagnostic_cpd_ns','timing_tail_text']
rows=[]
for name in ['8051','xtea']:
 cohorts={}
 for cohort in ['original','fresh']:
  arms={}
  for mode in ['cold','seed']:
   w=C/mode/'native'/name if cohort=='fresh' else R/f'experiments/freecores_native_{mode}_v1_2026-10-08'/name
   rp=w/'receipt.json';receipt=json.loads(rp.read_text());assert receipt['exit_code']==0
   for group in ['bindings','files']:assert all(sha(k)==h for k,h in receipt[group].items())
   log=w/'native.log';text=log.read_text();bindings[str(rp)]=sha(rp);bindings[str(log)]=sha(log)
   assert 'Iter   Time    pres' in text and 'VPR succeeded' in text
   records=[]
   for line in text.splitlines():
    m=pattern.match(line)
    if not m:continue
    data=dict(zip(keys,m.groups()))
    for k in ['iteration','bb_updates','heap_pushes','nets_routed','connections_routed','overused_node_count','wirelength']:data[k]=int(data[k])
    for k in ['rounded_iteration_seconds','rounded_pres_fac','rounded_overused_percent','rounded_wire_percent','rounded_diagnostic_cpd_ns']:data[k]=float(data[k])
    records.append(data)
   n=int(re.search(r'Successfully routed after (\d+) routing iterations',text)[1]);assert [x['iteration'] for x in records]==list(range(1,n+1)) and records[-1]['overused_node_count']==0 and all(x['overused_node_count']>0 for x in records[:-1])
   total=re.search(r'Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)',text);assert total
   sums={k:sum(x[k] for x in records) for k in ['nets_routed','connections_routed','heap_pushes']};assert list(sums.values())==list(map(int,total.groups()[:3]))
   ep=C/mode/'demand'/name/'endpoints.json' if cohort=='fresh' else R/'experiments/freecores_native_demand_v1_2026-10-08'/name/'endpoints.json';required=len(json.loads(ep.read_text())['connections']);bindings[str(ep)]=sha(ep)
   summary=dict(iterations=n,first_iteration=records[0],total_route_events=sums,total_heap_pops=int(total[4]),threshold_first_hit={str(t):next(x['iteration'] for x in records if x['overused_node_count']<=t) for t in [100,10,1,0]},native_seconds=receipt['native_process_seconds'],required_connections=required)
   assert all(x['connections_routed']<=required for x in records)
   if mode=='seed':
    sf=w/'subset.json';s=json.loads(sf.read_text());retained=len(s['records']);pending=len(s['pending']);assert retained+pending==required;bindings[str(sf)]=sha(sf)
    assert 'NET-aware seed imported feasible=1' in text
    summary.update(seed_connections=retained,pending_connections=pending,first_iteration_seed_route_event_lower_bound=max(0,records[0]['connections_routed']-pending),first_iteration_seed_avoided_route_event_upper_bound=required-records[0]['connections_routed'])
   else:assert records[0]['connections_routed']==required and 'NET-aware seed imported' not in text
   arms[mode]=dict(summary=summary,records=records)
  cohorts[cohort]=arms
 # Scientific replication concerns only printed discrete router counters, no stability claim from clocks.
 stablekeys=['iteration','bb_updates','heap_pushes','nets_routed','connections_routed','overused_node_count','wirelength']
 for mode in ['cold','seed']:
  a,b=[cohorts[c][mode]['records'] for c in ['original','fresh']];assert [{k:x[k] for k in stablekeys} for x in a]==[{k:x[k] for k in stablekeys} for x in b]
 c,s=[cohorts['fresh'][m]['summary'] for m in ['cold','seed']]
 rows.append(dict(name=name,cohorts=cohorts,original_and_fresh_discrete_trajectory_identical=True,iteration_delta=s['iterations']-c['iterations'],connection_route_event_delta=s['total_route_events']['connections_routed']-c['total_route_events']['connections_routed'],heap_push_delta=s['total_route_events']['heap_pushes']-c['total_route_events']['heap_pushes'],first_iteration_overused_node_delta=s['first_iteration']['overused_node_count']-c['first_iteration']['overused_node_count']))
assert all(sha(k)==h for k,h in bindings.items())
(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Post-hoc all 8 authenticated logs, per-iteration counters sum to separately printed native totals. Overused node counts differ from model overflow units. Counter events are not distinct NETs across iterations. First iteration seed-event lower bound by pigeonhole assuming each sink counted once per NET visit per iteration, matching native sink-loop source; no per-NET reroute identity/causal attribution from aggregate logs. Rounded time/CPD not precise clocks or silicon timing. No outcome-dependent policy change. Two identical discrete trajectories do not establish broad stability or unseen-family transfer.'),indent=2)+'\n')
print(json.dumps([{k:x[k] for k in ['name','original_and_fresh_discrete_trajectory_identical','iteration_delta','connection_route_event_delta','heap_push_delta','first_iteration_overused_node_delta']} for x in rows],indent=2))
