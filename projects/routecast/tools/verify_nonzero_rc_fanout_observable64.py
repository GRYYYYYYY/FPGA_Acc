"""Original XML single-path delay versus native route-tree FLOAT captures."""
import json,csv,re,math
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
from buffered_rc_node_classes import read,arc_delay
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_fanout_observable64_2026-10-06';receipt=json.loads((out/'receipt.json').read_text());protocol=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==receipt['protocol_sha256'];assert receipt['native_success'];assert all(sha(p)==h for p,h in receipt['files_sha256'].items());graph=Path(protocol['cwd'])/'rr_graph.xml';r={'results':[{'case':'nonzero_rc_fanout','cpd_ns':receipt['cpd_ns'],'cwd':protocol['cwd'],'inputs_sha256':{},'files_sha256':receipt['files_sha256'],'command':protocol['command']}]};ids,classes,switches,digest=read(graph);results=[]
def paths(path):
 nets={};cur=None;prev=None;switch=None;parents={}
 for line in path.read_text().splitlines():
  m=NET.match(line)
  if m:cur=int(m[1]);nets[cur]={'name':m[2],'paths':{}};prev=None;parents={}
  m=NODE.match(line)
  if not m:continue
  node=int(m[1]);kind=m[2]
  if kind=='SOURCE':parents[node]=[(node,None)]
  elif kind=='SINK':pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);nets[cur]['paths'][pin]=parents[prev]+[(node,switch)]
  elif node not in parents:parents[node]=parents[prev]+[(node,switch)]
  prev=node;switch=int(m[3])
 return nets
for row in r['results']:
 assert all(sha(p)==h for p,h in row['inputs_sha256'].items()) and all(sha(p)==h for p,h in row['files_sha256'].items());assert sha(row['command'][0])==protocol['binary_sha256'] and sha(row['command'][1])==protocol['architecture_sha256'];cwd=Path(row['cwd']);physical=audit(graph,cwd/'before_sync.route');assert physical['connections'] and not physical['overflow_units'];trees=paths(cwd/'before_sync.route');before=list(csv.DictReader((cwd/'before_sync.delays.tsv').open(),delimiter='\t'));after=list(csv.DictReader((cwd/'after_sync.delays.tsv').open(),delimiter='\t'));assert before==after;values={(int(x['net']),int(x['pin'])):x for x in before if int(x['pin'])>0};assert len(values)==len(physical['connections']);diffs=[];critical=[]
 for net,tree in trees.items():
  for pin,path in tree['paths'].items():
   rr=path[0][0];res,cap=classes[ids[rr]];delay=res*cap/2
   for rr,switch in path[1:]:delay+=arc_delay(classes,switches,ids[rr],switch)
   value=values.pop((net,pin));assert int(value['node'])==rr and value['name']==tree['name'];native=float(value['delay_s']);assert math.isfinite(native);difference=abs(native-float(delay));diffs.append(difference);assert difference<1e-14
   if tree['name']=='new_n761':critical.append({'pin':pin,'sink':rr,'native_delay_ns':native*1e9,'xml_path_delay_ns':float(delay)*1e9,'path':path})
 assert not values;results.append({'case':row['case'],'cpd_ns':row['cpd_ns'],'sink_delays_checked':len(diffs),'max_absolute_error_s':max(diffs),'new_n761':critical})
assert any(a>0 and b>0 for a,b in classes)
used={int(x['node']) for x in before};net_counts={tree['name']:len(tree['paths']) for tree in trees.values()};assert any(count>1 for count in net_counts.values());assert any(classes[ids[n]][0]>0 and classes[ids[n]][1]>0 for n in used)
summary={'used_nonzero_RC_nodes':sum(classes[ids[n]][0]>0 and classes[ids[n]][1]>0 for n in used),'native_nonzero_R_upstream_nodes':sum(float(x['R_upstream'])>0 for x in before),'native_nonzero_C_downstream_nodes':sum(float(x['C_downstream'])>0 for x in before),'routed_net_sink_counts':net_counts,'results':results,'nonzero_node_RC_classes':sum(a>0 and b>0 for a,b in classes),'graph_sha256':digest,'receipt_sha256':sha(out/'receipt.json'),'scope':'Fresh synthetic registered fanout microbenchmark on unmodified nonzero-RC 40nm architecture. Original XML single-path buffered delay replay compared with all native SINK FLOAT delays within1e-14 s, full physical arcs/capacity audited and native FULL pass. Buffered graph only; not unbuffered/passgate or arbitrary branch-load generalization, prospective repair benefit or speed claim.'};(out/'verification.json').write_text(json.dumps(summary,indent=2)+'\n');print('verified',sum(x['sink_delays_checked'] for x in results),'sink delays; nonzero RC classes',summary['nonzero_node_RC_classes'],'max error',max(x['max_absolute_error_s'] for x in results))
