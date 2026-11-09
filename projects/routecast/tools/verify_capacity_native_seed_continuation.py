"""Full original-XML route validation and matched seed-retention/quality evidence."""
import json,re,statistics
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
from audit_native_route import NODE,NET
root=Path(__file__).resolve().parents[1];out=root/'experiments/capacity_native_seed_continuation_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert sha(root/'tools/trial_capacity_native_seed_continuation.py')==r['source_sha256'];pairs={};checked=0

def traces(path):
 result={};cur=None;prev=None;switch=None;parents={}
 for line in path.read_text().splitlines():
  m=NET.match(line)
  if m:cur=int(m[1]);assert cur not in result;result[cur]={};prev=None;parents={}
  m=NODE.match(line)
  if not m:continue
  node=int(m[1]);kind=m[2]
  if kind=='SOURCE':parents[node]=[(node,None)]
  elif kind=='SINK':
   pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]);result[cur][pin]=parents[prev]+[(node,switch)]
  elif node not in parents:parents[node]=parents[prev]+[(node,switch)]
  prev=node;switch=int(m[3])
 return result
for row in r['results']:
 assert all(sha(p)==h for p,h in row['inputs_sha256'].items()) and all(sha(p)==h for p,h in row['artifacts_sha256'].items());cmd=row['command'];assert sha(cmd[0])==r['binary_sha256'];assert cmd[cmd.index('--check_route')+1]=='full';cwd=Path(row['cwd']);log=(cwd/'run.log').read_text();assert row['exit_code']==0 and row['native_success'] and 'Completed routing consistency check successfully.' in log and 'RouterOpts.check_route: FULL' in log and 'VPR succeeded' in log;graph=cmd[cmd.index('--read_rr_graph')+1];a=audit(graph,cwd/'output.route');assert len(a['connections'])==516 and a['overflow_units']==0;checked+=len(a['connections']);assert row['search_counts'];pairs.setdefault(row['pair_index'],{})[row['mode']]=row
 if row['mode']=='seed':
  assert 'NET-aware seed imported feasible=1' in log and 'initialized net_delay from seed before STA' in log;assert all(c==[0,0,0,0] for c in row['search_counts']);assert row['cpd_ns']==row['input_cpd_ns'];assert traces(cwd/'seed.route')==traces(cwd/'output.route');assert 'Found 0 mismatches' in log and 'Fixed 0 routing traces' in log
assert len(pairs)==20 and all(set(p)=={'cold','seed'} for p in pairs.values());comparison=[]
for index,pair in sorted(pairs.items()):
 cold,seed=pair['cold'],pair['seed'];assert {Path(p).name:h for p,h in cold['inputs_sha256'].items()}=={Path(p).name:h for p,h in seed['inputs_sha256'].items()};comparison.append({'pair_index':index,'cold_cpd_ns':cold['cpd_ns'],'seed_cpd_ns':seed['cpd_ns'],'seed_minus_cold_cpd_ns':seed['cpd_ns']-cold['cpd_ns'],'cold_counts':cold['search_counts'],'seed_counts':seed['search_counts'],'cold_wall_s':cold['wall_s'],'seed_wall_s':seed['wall_s']})
summary={'pairs':len(pairs),'physical_connections_checked':checked,'seed_better':sum(p['seed_minus_cold_cpd_ns']<-1e-5 for p in comparison),'equal':sum(abs(p['seed_minus_cold_cpd_ns'])<=1e-5 for p in comparison),'seed_worse':sum(p['seed_minus_cold_cpd_ns']>1e-5 for p in comparison),'cold_mean_wall_s':statistics.mean(p['cold_wall_s'] for p in comparison),'seed_mean_wall_s':statistics.mean(p['seed_wall_s'] for p in comparison),'results':comparison,'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'scope':'Complete native route-stage seed retention with zero searches; actual original XML audits on all forty outputs. Single process per arm/pair; timing excludes prediction/bundle preparation and is not matched-quality total-pipeline benefit. Worse seeded CPD means capacity-feasible early success does not provide timing repair or non-regression guarantee.'};(out/'verification.json').write_text(json.dumps(summary,indent=2)+'\n');print({k:v for k,v in summary.items() if k not in ('results','scope')})
