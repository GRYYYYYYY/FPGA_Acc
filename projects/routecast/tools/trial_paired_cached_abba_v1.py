"""Actual fixed-order ABBA full-workflow measurement with authenticated quality gates."""
import json,subprocess,sys,time,statistics
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];mp=R/'tools/paired_cached_abba_manifest_v1.json';m=json.loads(mp.read_text());D=R/'experiments/paired_cached_abba_v1_2026-10-09';D.mkdir(exist_ok=False);bindings={**closure([Path(__file__),*[R/c for p in m['plans'] for c in p['commands']]]),str(mp):sha(mp)}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,manifest=m),indent=2)+'\n');rows=[];identities=[]
for plan in m['plans']:
 start=time.perf_counter();codes=[]
 with (D/f"arm_{plan['arm']}.log").open('x') as log:
  for command in plan['commands']:
   code=subprocess.run([sys.executable,str(R/command)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode;codes.append(code)
   if code:break
 elapsed=time.perf_counter()-start
 row=dict(arm=plan['arm'],mode=plan['mode'],workflow_seconds=elapsed,exit_codes=codes);rows.append(row);(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(row,flush=True);assert len(codes)==len(plan['commands']) and not any(codes)
 reportp=R/'experiments'/plan['report'];report=json.loads(reportp.read_text());assert all(sha(p)==h for p,h in report['bindings'].items());bindings.update(report['bindings']);bindings[str(reportp)]=sha(reportp)
 quality=report['rows'][0] if plan['mode']=='online' else report
 assert quality['exact_model_budget_pass'] and quality['canonical_zero_counters'] and quality['full_named_paths_preserved'] and quality['native_and_canonical_connections']==[516,516] and quality['cpd_ns']==4.87739
 assert quality['wirelength']==(2630 if plan['mode']=='online' else 2646)
 row['quality']=dict(cpd_ns=quality['cpd_ns'],wirelength=quality['wirelength'],connections=quality['native_and_canonical_connections'])
 native=R/'experiments'/plan['native'];pp=native/'protocol.json';p=json.loads(pp.read_text())['plans'][0];identities.append({k:p[k] for k in ['step','endpoints','budget','command']});bindings[str(pp)]=sha(pp)
 if plan['mode']=='cold':assert 'seed' not in p
 for name in ['design.blif','design.net','design.place']:bindings[str(native/'step_3'/name)]=sha(native/'step_3'/name)
assert all(x==identities[0] for x in identities)
for name in ['design.blif','design.net','design.place']:assert len({sha(R/'experiments'/p['native']/'step_3'/name) for p in m['plans']})==1
for path in [D/'protocol.json',D/'progress.json',*[D/f'arm_{i}.log' for i in range(4)]]:bindings[str(path)]=sha(path)
assert all(sha(p)==h for p,h in bindings.items());online=[r['workflow_seconds'] for r in rows if r['mode']=='online'];cold=[r['workflow_seconds'] for r in rows if r['mode']=='cold'];out=dict(bindings=bindings,rows=rows,online_mean_seconds=statistics.mean(online),cold_mean_seconds=statistics.mean(cold),online_to_cold_ratio=statistics.mean(online)/statistics.mean(cold),identical_commands_and_input_bytes=True,scope=m['scope'])
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2),flush=True)
