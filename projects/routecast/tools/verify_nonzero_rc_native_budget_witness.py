"""Complete original native route as an exact1ns feasibility witness, not a prediction."""
import json,csv,re
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
from stream_native_route_audit import audit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];parent=root/'experiments/nonzero_rc_fanout_observable64_2026-10-06';r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==v['receipt_sha256'] and all(sha(p)==h for p,h in r['files_sha256'].items());work=root/'work/nonzero_rc_fanout_observable64_2026-10-06';graph=work/'rr_graph.xml';route=work/'before_sync.route';physical=audit(graph,route);assert len(physical['connections'])==69 and physical['overflow_units']==0;ids,classes,switches,digest=read(graph);required={(int(x['net']),int(x['pin'])):int(x['node']) for x in csv.DictReader((work/'before_sync.delays.tsv').open(),delimiter='\t') if int(x['pin'])>0};parents={};current=None;prev=None;sw=None;checked=[]
for line in route.read_text().splitlines():
 m=NET.match(line)
 if m:current=int(m[1]);parents={}
 m=NODE.match(line)
 if not m:continue
 n=int(m[1]);kind=m[2]
 if kind=='SOURCE':parents[n]=[(n,None)]
 elif kind=='SINK':
  pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);path=parents[prev]+[(n,sw)];assert required.pop((current,pin))==n;assert len({u for u,_ in path})==len(path);res,cap=classes[ids[path[0][0]]];delay=res*cap/2
  for node,switch in path[1:]:delay+=arc_delay(classes,switches,ids[node],switch)
  assert delay<=Fraction(1,10**9);checked.append({'net_id':current,'pin_index':pin,'sink':n,'delay_fraction_s':[delay.numerator,delay.denominator],'delay_ns':float(delay)*1e9})
 elif n not in parents:parents[n]=parents[prev]+[(n,sw)]
 prev=n;sw=int(m[3])
assert not required and len(checked)==69;out=root/'experiments/nonzero_rc_native_budget_witness_2026-10-06';out.mkdir();(out/'verification.json').write_text(json.dumps({'connections':69,'overflow_units':0,'max_exact_branch_delay_ns':max(x['delay_ns'] for x in checked),'results':checked,'graph_sha256':digest,'route_sha256':sha(route),'parent_verification_sha256':sha(parent/'verification.json'),'source_sha256':sha(Path(__file__)),'scope':'Original complete native reference route satisfies every1ns exact buffered-path constraint and original XML capacity, all NET/pin occurrences accounted; native FULL evidenced by parent. This is a reference witness proving this host constraint instance feasible, not a newly predicted solution or solver completeness/generalization claim.'},indent=2)+'\n');print('native complete1ns witness:',len(checked),'max ns',max(x['delay_ns'] for x in checked))
