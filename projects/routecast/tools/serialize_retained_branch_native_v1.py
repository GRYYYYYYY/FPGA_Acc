"""Serialize verified retained forests with original native trace formatting."""
import json,re
from collections import defaultdict,Counter
from pathlib import Path
from audit_native_route import NET,NODE
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1]
C=R/'experiments/retained_branch_sink_identity_v2_2026-10-08/certificate.json'
c=json.loads(C.read_text());assert c['all_twelve_unique_sink_identity_maps_pass']
bindings={**c['bindings'],str(C):sha(C),str(Path(__file__)):sha(Path(__file__))}
P=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
D=R/'experiments/retained_branch_native_serialization_v1_2026-10-08';D.mkdir(exist_ok=False)
rows=[]
for case in json.loads(P.read_text())['cases']:
 w,i=case['width'],case['index'];old,target=[json.loads(Path(case[k]).read_text()) for k in ('old','target')]
 original=Path(old['inputs']['graph']['path']).with_name('design.route');paths=physical_paths(original)
 forest=R/f'experiments/endpoint_compatible_branch_trim_v1_2026-10-08/w{w}_m{i}.json'
 mapping=R/f'experiments/retained_branch_sink_identity_v2_2026-10-08/w{w}_m{i}.json'
 retained=json.loads(forest.read_text())['retained'];pins=json.loads(mapping.read_text());templates=defaultdict(dict);headers={};name=None;head=[]
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
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_twelve_serialized_paths_pass=True,scope='Incomplete target-bound route; serializer path/index checks only. Native target loader, FULL repair, packed IPIN reconciliation and STA remain unverified.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
