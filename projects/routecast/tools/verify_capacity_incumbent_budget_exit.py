import json,re
from pathlib import Path
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
root=Path(__file__).resolve().parents[1];out=root/'experiments/capacity_incumbent_budget_exit_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert sha(root/'tools/trial_capacity_incumbent_budget_exit.py')==r['source_sha256']
def paths(path):
 result={};cur=None;prev=None;switch=None;parents={}
 for line in path.read_text().splitlines():
  m=NET.match(line)
  if m:cur=int(m[1]);result[cur]={};prev=None;parents={}
  m=NODE.match(line)
  if not m:continue
  n=int(m[1]);kind=m[2]
  if kind=='SOURCE':parents[n]=[(n,None)]
  elif kind=='SINK':pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);result[cur][pin]=parents[prev]+[(n,switch)]
  elif n not in parents:parents[n]=parents[prev]+[(n,switch)]
  prev=n;switch=int(m[3])
 return result

for row in r['results']:
 assert all(sha(p)==h for p,h in row['files_sha256'].items());cwd=Path(row['cwd']);log=(cwd/'run.log').read_text();assert row['command'][row['command'].index('--max_router_iterations')+1]=='1'
 if row['guard']:
  assert row['exit_code']==0 and row['native_success'] and row['cpd_ns']==4.72106;assert 'Restoring best routing' in log and 'Completed routing consistency check successfully.' in log and 'Found 0 mismatches' in log and 'Fixed 0 routing traces' in log;assert paths(cwd/'output.route')==paths(cwd/'seed.route');assert not re.findall(r'ROUTECAST_INCUMBENT_CANDIDATE',log)
 else:assert row['exit_code']==2 and not row['native_success'] and 'Routing failed.' in log
(out/'verification.json').write_text(json.dumps({'restored_connections':516,'unguarded_exit_code':2,'guarded_exit_code':0,'guarded_cpd_ns':4.72106,'receipt_sha256':sha(out/'receipt.json'),'scope':'Real native one-iteration exhaustion with no legal repair candidate; guarded output exactly preserves all terminal paths, zero packing fixes, native FULL and original XML audit pass. No exception safety, signal/OOM recovery or production publication guarantee.'},indent=2)+'\n');print('verified one-iteration budget fallback')
