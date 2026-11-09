"""Verify actual native incumbent rejection/restore and accepted improvement."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from audit_native_route import NET,NODE
root=Path(__file__).resolve().parents[1];out=root/'experiments/capacity_seed_incumbent_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert sha(root/'tools/trial_capacity_seed_incumbent.py')==r['source_sha256'];build=root/'build/capacity_seed_incumbent_2026-10-06';assert sha(build/'receipt.json')==r['build_receipt_sha256'];br=json.loads((build/'receipt.json').read_text());assert sha(build/'route.cpp')==br['source_sha256'] and all(sha(p)==h for p,h in br['inputs_sha256'].items());pairs={}
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
 assert all(sha(p)==h for p,h in row['files_sha256'].items());assert sha(row['command'][0])==r['binary_sha256']==br['binary_sha256'];cwd=Path(row['cwd']);log=(cwd/'run.log').read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log and 'RouterOpts.check_route: FULL' in log;output=paths(cwd/'output.route');seed=paths(cwd/'seed.route');assert sum(len(p) for p in output.values())==516;key=(row['pair_index'],row['max_criticality']);pairs.setdefault(key,{})[row['guard']]=row
 if row['guard']:
  assert 'ROUTECAST_SEED_INCUMBENT cpd_ns=' in log and row['cpd_ns']<=row['seed_cpd_ns']+1e-5;assert row['candidates'];rejects=[x for x in row['candidates'] if not x['admissible']]
  for c in row['candidates']:assert c['admissible']==(c['cpd_ns']<=row['seed_cpd_ns']+1e-6)
  if row['max_criticality']=='0':assert rejects and output==seed and abs(row['cpd_ns']-row['seed_cpd_ns'])<1e-5;assert 'Found 0 mismatches' in log and 'Fixed 0 routing traces' in log
assert len(pairs)==4 and all(set(p)=={False,True} for p in pairs.values());results=[]
for (pair,crit),arms in sorted(pairs.items()):
 off,on=arms[False],arms[True];assert all(sha(Path(off['cwd'])/n)==sha(Path(on['cwd'])/n) for n in ('design.net','design.place','design.blif','seed.route','repair_names.txt'));assert off['command']==on['command'];results.append({'pair_index':pair,'max_criticality':crit,'seed_cpd_ns':on['seed_cpd_ns'],'unguarded_cpd_ns':off['cpd_ns'],'guarded_cpd_ns':on['cpd_ns'],'rejected_legal_iterations':sum(not x['admissible'] for x in on['candidates'])})
assert pairs[(8,'0.99')][True]['cpd_ns']<pairs[(8,'0.99')][True]['seed_cpd_ns']-1e-5
(out/'verification.json').write_text(json.dumps({'paired_cases':len(pairs),'restored_seed_cases':sum(x['max_criticality']=='0' for x in results),'restored_terminal_paths':1032,'results':results,'receipt_sha256':sha(out/'receipt.json'),'scope':'Same binary/input/options guard-on/off; legal seed FULL/STA capture, accepted normal improvement, rejected actual worse legal iterations, exact all 1032 restored terminal-indexed paths. Trial original XML audit validates all eight outputs. No exception-safe transaction, timing guarantee against previous placement/cold, hold/whole PPA guarantee or coherent postpacked bundle reload proof.'},indent=2)+'\n');print(results)
