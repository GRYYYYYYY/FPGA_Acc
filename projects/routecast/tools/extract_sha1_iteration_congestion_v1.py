"""Exact printed aggregate iteration labels, not resource-level occupancy."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha1_actual_old_linear_expat_workflow_v1_2026-10-10';proof=D/'verification.json';v=json.loads(proof.read_text());assert v['all_cases_both_complete_arms_authenticated']
bindings={**v['bindings'],str(proof):sha(proof),str(Path(__file__)):sha(Path(__file__))};assert all(sha(k)==h for k,h in bindings.items())
pattern=re.compile(r'^\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\(\s*([\d.]+)%\)\s+(\d+)\s+\(\s*([\d.]+)%\)\s+([\d.]+)\s+(.+)$')
rows=[]
for case in v['cases']:
 for arm,info in case['arms'].items():
  p=D/arm/'native'/case['name']/'native.log';text=p.read_text();bindings[str(p)]=sha(p)
  header='Iter   Time';start=text.index(header);end=text.index('Restoring best routing',start);lines=text[start:end].splitlines();records=[]
  for offset,line in enumerate(lines):
   if not re.match(r'^\s*\d+\s',line):continue
   m=pattern.fullmatch(line);assert m,repr(line);x=m.groups()
   records.append(dict(iteration=int(x[0]),printed_time_seconds=float(x[1]),printed_pres_fac=float(x[2]),bbox_updates=int(x[3]),heap_pushes=int(x[4]),rerouted_nets=int(x[5]),rerouted_connections=int(x[6]),overused_rr_nodes=int(x[7]),printed_overused_percent=float(x[8]),wirelength=int(x[9]),printed_wire_percent=float(x[10]),printed_diagnostic_cpd_ns=float(x[11]),remaining_printed_fields=x[12],log_line=text[:start].count('\n')+offset+1,raw_line=line))
  assert [x['iteration'] for x in records]==list(range(1,info['iterations']+1))
  assert records[-1]['overused_rr_nodes']==0 and records[-1]['wirelength']==info['wirelength']
  assert abs(records[-1]['printed_diagnostic_cpd_ns']-info['diagnostic_cpd_ns'])<=0.0005
  rows.append(dict(case=case['name'],arm=arm,records=records,summary=dict(iterations=len(records),sum_heap_pushes=sum(x['heap_pushes'] for x in records),sum_rerouted_nets=sum(x['rerouted_nets'] for x in records),sum_rerouted_connections=sum(x['rerouted_connections'] for x in records),sum_iteration_overused_node_counts=sum(x['overused_rr_nodes'] for x in records),initial_overused_rr_nodes=records[0]['overused_rr_nodes'])))
assert all(sha(k)==h for k,h in bindings.items())
out=D/'iteration_congestion_v1.json';out.write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Printed native per-iteration aggregate RR overused-node counts and router work. Overused-node count is not excess occupancy units, unique resources across rounds, or CHAN-only spatial truth. Rounded times/CPD not accurate wall clocks or characterized timing. Successful width128 cases only; not route-failure labels or heldout validation.'),indent=2)+'\n')
print(json.dumps([dict(case=x['case'],arm=x['arm'],**x['summary']) for x in rows],indent=2))
