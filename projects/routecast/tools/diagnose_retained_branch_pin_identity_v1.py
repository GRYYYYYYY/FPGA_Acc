"""Bind retained query identity to original native sink pins through packed IPIN identity."""
import json,re
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import extract,sha
from audit_native_route import NET,NODE
R=Path(__file__).resolve().parents[1]
P=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
V=R/'experiments/endpoint_compatible_branch_trim_v1_2026-10-08/verification.json'
v=json.loads(V.read_text());assert v['complete_twelve_cases_independent_branch_forest_pass']
bindings={**v['bindings'],str(V):sha(V),str(P):sha(P),str(Path(__file__)):sha(Path(__file__))}
D=R/'experiments/retained_branch_pin_identity_v1_2026-10-08';D.mkdir(exist_ok=True)
rows=[];cache={}
for case in json.loads(P.read_text())['cases']:
 old=json.loads(Path(case['old']).read_text());w=case['width']
 if w not in cache:
  inputs=old['inputs'];rebuilt,meta=extract(*(Path(inputs[k]['path']) for k in ('net','place','graph')))
  assert rebuilt['connections']==old['connections'] and rebuilt['net_names']==old['net_names']
  bynet=defaultdict(list)
  for p in meta['pin_details']:
   if p['role']=='SINK':bynet[p['net_id']].append(p)
  pins={};offset=defaultdict(int)
  for q in old['connections']:
   p=bynet[q['net_id']][offset[q['net_id']]];offset[q['net_id']]+=1
   assert p['rr_node']==q['sink'];pins[q['connection_id']]=p
  expected=defaultdict(list)
  for q in old['connections']:
   p=pins[q['connection_id']];expected[old['net_names'][str(q['net_id'])],q['sink'],p['physical_pin_ptc']].append(q['connection_id'])
  route=Path(inputs['graph']['path']).with_name('design.route');bindings[str(route)]=sha(route)
  name=None;previous=None;found={};native_pins=set();unmatched=[]
  for line in route.read_text().splitlines():
   n=NET.match(line)
   if n:name=n[2];previous=None
   m=NODE.match(line)
   if not m:continue
   node,kind=int(m[1]),m[2]
   if kind=='SINK':
    assert previous is not None and previous[0]=='IPIN'
    ptc=previous[1];pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1])
    candidates=expected[name,node,ptc]
    if len(candidates)!=1:
     unmatched.append(dict(net=name,sink=node,ipin_ptc=ptc,native_sink_pin_index=pin,candidates=candidates));previous=(kind,None);continue
    cid=candidates[0];assert cid not in found and (name,pin) not in native_pins
    found[cid]=dict(native_net_name=name,native_sink_pin_index=pin,physical_ipin_ptc=ptc,sink=node)
    native_pins.add((name,pin))
   if kind=='IPIN':
    mptc=re.search(r'(?:Pin|Pad):\s*(\d+)',line);assert mptc
    previous=(kind,int(mptc[1]))
   else:previous=(kind,None)
  assert set(found)<=set(pins)
  cache[w]=(found,unmatched,len(pins))
 found,unmatched,required=cache[w];forest=R/f'experiments/endpoint_compatible_branch_trim_v1_2026-10-08/w{w}_m{case["index"]}.json';bindings[str(forest)]=sha(forest)
 retained=json.loads(forest.read_text())['retained'];mapped={str(q['connection_id']):found[q['connection_id']] for q in retained if q['connection_id'] in found}
 path=D/f'w{w}_m{case["index"]}.json';path.write_text(json.dumps(dict(matches=mapped,unmatched_original_native_pins=unmatched),indent=2)+'\n');bindings[str(path)]=sha(path)
 rows.append(dict(width=w,index=case['index'],required_old_queries=required,matched_old_queries=len(found),unmatched_native_pins=len(unmatched),retained_pin_matches=len(mapped)))
assert all(sha(p)==h for p,h in bindings.items())
(D/'diagnosis.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_old_queries_unique_physical_pin_matched=all(x["required_old_queries"]==x["matched_old_queries"] for x in rows),scope='Diagnostic strict pre-route physical IPIN identity matches only; unmatched pins require equivalent-site/post-routing identity reconciliation, no complete native pin mapping or partial serialization proof'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
