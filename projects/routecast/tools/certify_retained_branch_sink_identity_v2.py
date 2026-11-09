"""Unique named endpoint to native sink-index mapping; never match by arbitrary order."""
import json,re
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import extract,sha
from audit_native_route import NET,NODE
R=Path(__file__).resolve().parents[1]
P=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json'
V=R/'experiments/endpoint_compatible_branch_trim_v1_2026-10-08/verification.json'
v=json.loads(V.read_text());assert v['complete_twelve_cases_independent_branch_forest_pass']
bindings={**v['bindings'],str(V):sha(V),str(P):sha(P),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/pre_route_endpoints.py'):sha(R/'tools/pre_route_endpoints.py')}
D=R/'experiments/retained_branch_sink_identity_v2_2026-10-08';D.mkdir(exist_ok=False)
rows=[];cache={}
def details(ep):
 rebuilt,meta=extract(*(Path(ep['inputs'][k]['path']) for k in ('net','place','graph')))
 assert rebuilt['connections']==ep['connections'] and rebuilt['net_names']==ep['net_names']
 grouped=defaultdict(list)
 for p in meta['pin_details']:
  if p['role']=='SINK':grouped[p['net_id']].append(p)
 result={};offset=defaultdict(int)
 for q in ep['connections']:
  p=grouped[q['net_id']][offset[q['net_id']]];offset[q['net_id']]+=1
  assert p['rr_node']==q['sink'];result[q['connection_id']]=(p['net'],p['block'],p['port'],p['bit'])
 return result
for c in json.loads(P.read_text())['cases']:
 old,target=[json.loads(Path(c[k]).read_text()) for k in ('old','target')];w=c['width']
 if w not in cache:
  route=Path(old['inputs']['graph']['path']).with_name('design.route');bindings[str(route)]=sha(route)
  query={}
  for q in old['connections']:
   key=(old['net_names'][str(q['net_id'])],q['source'],q['sink']);assert key not in query
   query[key]=q['connection_id']
  found={};seen=set();name=source=None
  for line in route.read_text().splitlines():
   n=NET.match(line)
   if n:name=n[2];source=None
   m=NODE.match(line)
   if not m:continue
   if m[2]=='SOURCE':assert source is None;source=int(m[1])
   if m[2]=='SINK':
    cid=query[(name,source,int(m[1]))];pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1])
    assert pin>0 and cid not in found and (name,pin) not in seen
    found[cid]=dict(net_name=name,native_sink_pin_index=pin,source=source,sink=int(m[1]));seen.add((name,pin))
  assert set(found)=={q['connection_id'] for q in old['connections']}
  cache[w]=(found,details(old))
 found,old_details=cache[w];target_details=details(target);assert target_details==old_details
 forest=R/f'experiments/endpoint_compatible_branch_trim_v1_2026-10-08/w{w}_m{c["index"]}.json';bindings[str(forest)]=sha(forest)
 mapped={}
 for q in json.loads(forest.read_text())['retained']:
  cid=q['connection_id'];p=found[cid];assert (p['source'],p['sink'])==(q['source'],q['sink'])
  mapped[str(cid)]={**p,'packed_sink_identity':list(old_details[cid])}
 out=D/f'w{w}_m{c["index"]}.json';out.write_text(json.dumps(mapped,indent=2)+'\n');bindings[str(out)]=sha(out)
 rows.append(dict(width=w,index=c['index'],complete_old_query_sink_index_matches=len(found),retained_sink_index_matches=len(mapped),all_target_packed_sink_identities_unchanged=True))
assert all(sha(p)==h for p,h in bindings.items())
(D/'certificate.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_twelve_unique_sink_identity_maps_pass=True,scope='Unique original named SOURCE/SINK plus stable packed block/port/bit identity. Native target pin index order must still be checked by loader; no physical IPIN equivalence or partial native routing proof.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
