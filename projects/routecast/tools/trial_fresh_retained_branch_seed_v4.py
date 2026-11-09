"""Serialize verified retained forests with original native trace formatting."""
import json,re
from collections import defaultdict,Counter
from pathlib import Path
from audit_native_route import NET,NODE
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1]
import time,sys
from fractions import Fraction as F
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
started=time.perf_counter()
P=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
bindings={**closure([Path(__file__)]),str(P):sha(P)}
D=R/'experiments/fresh_retained_branch_seed_v4_2026-10-08';D.mkdir(exist_ok=False)
rows=[]
for case in [next(c for c in json.loads(P.read_text())['cases'] if c['width']==32 and c['index']==2)]:
 w,i=case['width'],case['index'];old,target=[json.loads(Path(case[k]).read_text()) for k in ('old','target')]
 original=Path(old['inputs']['graph']['path']).with_name('design.route');paths=physical_paths(original)
 for key in ('old','target','budget'):bindings[case[key]]=sha(case[key])
 bindings[str(original)]=sha(original)
 assert old['graph_sha256']==target['graph_sha256'] and old['inputs']['net']['sha256']==target['inputs']['net']['sha256']
 graph,digest,nodes,fields,rc,queries=load_endpoints(Path(case['old']));bindings[str(graph)]=digest
 state,initial,ledger=load_complete(original,old,nodes,fields,rc)
 byid={q['connection_id']:q for q in queries};target_byid={q['connection_id']:q for q in target['connections']};delays={r['connection_id']:r for r in initial};assert set(byid)==set(target_byid)
 budget=json.loads(Path(case['budget']).read_text());retained=[];released=[];pins={};query_keys={(old['net_names'][str(q['net_id'])],q['source'],q['sink']):cid for cid,q in byid.items()};assert len(query_keys)==len(byid)
 name=source=None
 for line in original.read_text().splitlines():
  n=NET.match(line)
  if n:name=n[2];source=None
  m=NODE.match(line)
  if not m:continue
  if m[2]=='SOURCE':assert source is None;source=int(m[1])
  if m[2]=='SINK':
   cid=query_keys[name,source,int(m[1])];pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);assert pin>0 and str(cid) not in pins
   pins[str(cid)]=dict(net_name=name,native_sink_pin_index=pin)
 assert len(pins)==len(byid)
 for cid,q in sorted(target_byid.items()):
  before=byid[cid];assert old['net_names'][str(before['net_id'])]==target['net_names'][str(q['net_id'])]
  if (q['source'],q['sink'])!=(before['source'],before['sink']):released.append(dict(connection_id=cid,reason='ENDPOINT_CHANGED'));continue
  delay=F(delays[cid]['delay_integer'],rc.scale);limit=F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))
  if delay*10**9>limit:released.append(dict(connection_id=cid,reason='TARGET_BUDGET_UNSAFE',delay_seconds=str(delay),budget_ns=str(limit)));continue
  retained.append(dict(q,physical_edge_ids=delays[cid]['physical_edge_ids'],delay_seconds=str(delay),budget_ns=str(limit)))
 (D/'forest.json').write_text(json.dumps(dict(retained=retained,released=released),indent=2)+'\n')
 templates=defaultdict(dict);headers={};name=None;head=[]
 for line in original.read_text().splitlines():
  n=NET.match(line)
  if n:name=n[2];headers[name]=line;continue
  m=NODE.match(line)
  if m:
   node=int(m[1]);base=re.sub(r'Switch:\s*-?\d+','Switch: @SW@',line)
   if node in templates[name]:assert templates[name][node]==base
   templates[name][node]=base
  elif name is None:head.append(line)
 head[0]='Placement_File: design.place Placement_ID: SHA256:'+target['inputs']['place']['sha256']
 selected=defaultdict(list);expected_pins={}
 for q in retained:
  cid=q['connection_id'];p=pins[str(cid)];options=[x for x in paths[p['net_name']] if (x[0][0],x[-1][0])==(q['source'],q['sink'])];assert len(options)==1
  selected[p['net_name']].append(options[0]);expected_pins[p['net_name'],q['sink']]=p['native_sink_pin_index']
 lines=head[:]
 for name,branches in selected.items():
  children=defaultdict(dict);roots={x[0][0] for x in branches};assert len(roots)==1;root=next(iter(roots));parents={}
  for path in branches:
   for (u,_),(v,switch) in zip(path,path[1:]):
    assert v not in parents or parents[v]==(u,switch);parents[v]=(u,switch)
    assert v not in children[u] or children[u][v]==switch;children[u][v]=switch
  lines.extend([headers[name],''])
  def emit(u):
   if not children[u]:
    assert (name,u) in expected_pins
    line=templates[name][u].replace('@SW@','-1');assert int(re.search(r'Net_pin_index:\s*(\d+)',line)[1])==expected_pins[name,u]
    lines.append(line);return
   for v,switch in children[u].items():
    lines.append(templates[name][u].replace('@SW@',str(switch)));emit(v)
  emit(root);lines.append('')
 out=D/f'w{w}_m{i}.route';out.write_text('\n'.join(lines)+'\n')
 actual=physical_paths(out);assert {n:Counter(p) for n,p in actual.items()}=={n:Counter(p) for n,p in selected.items()}
 bindings[str(out)]=sha(out)
 rows.append(dict(width=w,index=i,retained_nets=len(selected),retained_connections=len(retained),route=str(out),route_sha256=sha(out),exact_original_paths_preserved=True))
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,fresh_single_case_retained_forest_and_serialization_pass=True,component_elapsed_seconds=time.perf_counter()-started,scope='Fresh provided old route/old and target endpoint/original budget to retained seed. No historical forest/pinmap/seed consumed. Original route pin indices and unchanged packed netlist authenticated. Single development case, requires independent physical/Fraction/packed identity and actual target loader proof; upstream endpoint/budget production excluded.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
