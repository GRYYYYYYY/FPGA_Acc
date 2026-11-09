"""Original VPR iteration counters, not unique NET counts or measured rip-up events."""
import json,re,sys
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/aes_native_demand_full_cold_comparison_v1_2026-10-08';comparison=out/'comparison.json';d=json.loads(comparison.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());bindings={str(comparison):sha(comparison),str(Path(__file__)):sha(Path(__file__))};rows=[]
for row in d['rows']:
 name=row['name'];counts={}
 for mode,folder in [('seed','aes_native_demand_full_workflow_v1_2026-10-08'),('cold','aes_native_demand_cold_full_workflow_v1_2026-10-08')]:
  log=R/'experiments'/folder/name/'native.log';text=log.read_text();start=text.index('Iter   Time    pres');end=text.index('Restoring best routing',start);table=text[start:end];records=[]
  for line in table.splitlines():
   if not re.match(r'^\s*\d+\s+',line):continue
   cols=line.split();assert len(cols)==19,(line,len(cols));records.append({'iteration':int(cols[0]),'printed_time_seconds':float(cols[1]),'present_cost_factor':float(cols[2]),'bbox_updates':int(cols[3]),'heap_pushes':int(cols[4]),'reported_rerouted_nets':int(cols[5]),'reported_rerouted_connections':int(cols[6]),'overused_nodes':int(cols[7])})
  n=int(re.search(r'Successfully routed after (\d+) routing iterations',text)[1]);assert [x['iteration'] for x in records]==list(range(1,n+1)) and n==row[mode+'_iterations'];assert records[-1]['overused_nodes']==0
  sums={field:sum(x[field] for x in records) for field in ['bbox_updates','heap_pushes','reported_rerouted_nets','reported_rerouted_connections']};later={field:sum(x[field] for x in records[1:]) for field in sums};counts[mode]={'iterations':records,'all_iterations_sum':sums,'iterations_2_onward_sum':later};bindings[str(log)]=sha(log)
 rows.append({'name':name,'reported_native_routing_work':counts})
assert all(sha(k)==v for k,v in bindings.items());(out/'routing_work.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'VPR printed routing counters. Iteration one includes initial construction; separate later-iteration sums. Repeated NETs/connections counted each iteration, not unique query counts. No instrumented rip-up event count or timing sum claimed; printed times rounded.'},indent=2)+'\n');print([(x['name'],{m:v['all_iterations_sum'] for m,v in x['reported_native_routing_work'].items()}) for x in rows])
