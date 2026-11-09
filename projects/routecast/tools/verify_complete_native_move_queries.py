import json,re
from pathlib import Path
from audit_native_route import NET,NODE
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_complete_move_queries_2026-10-06';r=json.loads((out/'receipt.json').read_text());checks=[];skipped=[]
for frame in r['frames']:
 design=frame['design'];step=frame['step'];p=out/f'{design}_{step}.json';assert sha(p)==frame['sha256'];data=json.loads(p.read_text());assert all(sha(f)==h for f,h in data['inputs_sha256'].items());log=(root/'experiments/native_candidate_resource_frames_2026-10-06'/design/'run.log').read_text();selected=re.findall(r'dynamic selection step=(\d+).*?blocks=(\d+),(\d+)',log);pair=next((int(a),int(b)) for s,a,b in selected if int(s)==step);matches=[m for m in data['moves'] if tuple(m['pair'])==pair or tuple(reversed(m['pair']))==pair]
 if not matches:skipped.append({'design':design,'step':step,'pair':pair,'reason':'actual four-pair candidate outside frozen diverse pool'});continue
 route=root/'work/native_candidate_resource_frames_2026-10-06'/design/f'candidate_{step}.route';current=None;sources={};sinks={}
 for line in route.read_text().splitlines():
  m=NET.match(line)
  if m:current=int(m[1])
  m=NODE.match(line)
  if m:
   node=int(m[1])
   if m[2]=='SOURCE':sources[current]=node
   elif m[2]=='SINK':pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);assert (current,pin) not in sinks;sinks[current,pin]=node
 for q in matches[0]['queries']:assert sources[q['net_id']]==q['source'] and sinks[q['net_id'],q['pin_index']]==q['sink']
 checks.append({'design':design,'step':step,'pair':pair,'connections_checked':len(matches[0]['queries']),'native_candidate_sha256':sha(route)})
assert checks
(out/'native_verification.json').write_text(json.dumps({'checks':checks,'outside_pool':skipped,'scope':'Independent actual native candidate SOURCE/SINK and pin-index identity checks only for intersecting frozen-pool moves; all other cohorts have construction/input checks but no direct native replay here.'},indent=2)+'\n');print('native cases',len(checks),'connections',sum(x['connections_checked'] for x in checks))
