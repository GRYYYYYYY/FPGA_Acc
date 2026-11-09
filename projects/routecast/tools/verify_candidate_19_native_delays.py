"""Original XML single-path delay versus native route-tree FLOAT captures."""
import json,csv,re,math
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
from buffered_rc_node_classes import read,arc_delay
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/candidate_19_native_delays_2026-10-06';r=json.loads((out/'receipt.json').read_text());graph=r['results'][0]['command'][r['results'][0]['command'].index('--read_rr_graph')+1];ids,classes,switches,digest=read(graph);results=[]
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
 assert all(sha(p)==h for p,h in row['inputs_sha256'].items()) and all(sha(p)==h for p,h in row['files_sha256'].items());assert sha(row['command'][0])==r['binary_sha256'];cwd=Path(row['cwd']);physical=audit(graph,cwd/'before_sync.route');assert len(physical['connections'])==516 and not physical['overflow_units'];trees=paths(cwd/'before_sync.route');before=list(csv.DictReader((cwd/'before_sync.delays.tsv').open(),delimiter='\t'));after=list(csv.DictReader((cwd/'after_sync.delays.tsv').open(),delimiter='\t'));assert before==after;values={(int(x['net']),int(x['pin'])):x for x in before if int(x['pin'])>0};assert len(values)==516;diffs=[];critical=[]
 for net,tree in trees.items():
  for pin,path in tree['paths'].items():
   rr=path[0][0];res,cap=classes[ids[rr]];delay=res*cap/2
   for rr,switch in path[1:]:delay+=arc_delay(classes,switches,ids[rr],switch)
   value=values.pop((net,pin));assert int(value['node'])==rr and value['name']==tree['name'];native=float(value['delay_s']);assert math.isfinite(native);difference=abs(native-float(delay));diffs.append(difference);assert difference<1e-14
   if tree['name']=='new_n761':critical.append({'pin':pin,'sink':rr,'native_delay_ns':native*1e9,'xml_path_delay_ns':float(delay)*1e9,'path':path})
 assert not values;results.append({'case':row['case'],'cpd_ns':row['cpd_ns'],'sink_delays_checked':len(diffs),'max_absolute_error_s':max(diffs),'new_n761':critical})
assert len(results)==4;target={x['case']:next(y for y in x['new_n761'] if y['sink']==338) for x in results};difference=target['critical']['native_delay_ns']-target['cold']['native_delay_ns'];assert abs(difference-0.2079)<1e-5;assert target['dirty']['path']==target['critical']['path'];summary={'results':results,'critical_sink_338_native_delta_ns':difference,'all_node_RC_zero':all(a==0 and b==0 for a,b in classes),'graph_sha256':digest,'receipt_sha256':sha(out/'receipt.json'),'scope':'All 2064 sink delays agree with original XML single-path buffered model within 1e-14 s, bounded FLOAT comparison, not exact FLOAT identity. This graph has zero node R/C; no nonzero-RC branch-load validation. new_n761 sink 338 delay gap 0.2079 ns matches rounded STA common-endpoint increment gap. Dirty+critical selection still produces same physical path, so missing NET selection alone is insufficient.'};(out/'verification.json').write_text(json.dumps(summary,indent=2)+'\n');print('verified',sum(x['sink_delays_checked'] for x in results),'native sink delays; delta ns',difference,'node RC zero',summary['all_node_RC_zero'])
