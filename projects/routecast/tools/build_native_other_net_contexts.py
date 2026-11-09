import json,re,struct,time
from pathlib import Path
from collections import Counter
from audit_native_route import NET,NODE
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];parent=root/'experiments/native_candidate_resource_frames_2026-10-06';verified=json.loads((parent/'resource_verification.json').read_text());assert all(sha(p)==h for p,h in verified['inputs_sha256'].items());out=root/'experiments/native_other_net_contexts_2026-10-06';out.mkdir();start=time.perf_counter();results=[]
def derive(total,own):
 other=dict(total)
 for node in own:
  if other.get(node,0)<1:raise ValueError('own NET missing from total occupancy')
  other[node]-=1
  if not other[node]:del other[node]
 return other
for frame in verified['frames']:
 design=frame['design'];step=frame['step'];cwd=root/'work/native_candidate_resource_frames_2026-10-06'/design;resources=cwd/f'state_{step}.resources.tsv';route=cwd/f'state_{step}.route';place=cwd/f'state_{step}.place';table=cwd/f'state_{step}.tsv';lines=resources.read_text().splitlines();header=lines[0].split('\t');epoch=int(header[1]);assert int(header[3])==step;total={};history={}
 for line in lines[2:]:
  node,occ,cost=line.split('\t');node=int(node);occ=int(occ)
  if occ:total[node]=occ
  bits=struct.unpack('<I',struct.pack('<f',float(cost)))[0]
  if bits!=0x3f800000:history[node]=bits
 nets={};names={};current=None
 for line in route.read_text().splitlines():
  match=NET.match(line)
  if match:current=int(match[1]);assert current not in nets;nets[current]=set();names[current]=match[2]
  match=NODE.match(line)
  if match:assert current is not None;nets[current].add(int(match[1]))
 demand=Counter(n for own in nets.values() for n in own);residual={n:v-demand.get(n,0) for n,v in total.items() if v> demand.get(n,0)};assert all(total.get(n,0)>=v for n,v in demand.items());checks=0
 for target,own in nets.items():
  actual=derive(total,own);expected=Counter(n for net,used in nets.items() if net!=target for n in used);expected.update(residual);assert actual==dict(+expected);assert all(v>0 for v in actual.values());checks+=1
 payload={'design':design,'epoch':epoch,'step':step,'node_count':frame['node_count'],'total_occupancy':total,'residual_demand':residual,'history_float32_bits':history,'net_names':names,'own_net_nodes':{n:sorted(v) for n,v in nets.items()},'inputs_sha256':{str(p):sha(p) for p in (resources,route,place,table,cwd/'design.net')},'scope':'Competing demand = native total minus one own-NET union membership, with residual reservations retained. Native NET namespace. Does not yet remove all dirty NETs for a placement move.'}
 file=out/f'{design}_{step}.json';file.write_text(json.dumps(payload,indent=2)+'\n');results.append({'design':design,'step':step,'epoch':epoch,'net_contexts_checked':checks,'residual_units':sum(residual.values()),'context_sha256':sha(file)})
(out/'receipt.json').write_text(json.dumps({'frames':results,'contexts_checked':sum(x['net_contexts_checked'] for x in results),'wall_s':time.perf_counter()-start,'resource_verification_sha256':sha(parent/'resource_verification.json'),'source_sha256':sha(Path(__file__))},indent=2)+'\n');print('verified',sum(x['net_contexts_checked'] for x in results),'NET contexts')
