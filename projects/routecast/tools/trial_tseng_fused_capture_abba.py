"""Frozen ABBA first-analysis sync capture versus separate capture pipeline."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_fused_capture_abba_2026-10-06';out.mkdir();runs=[]
for label,fused in [('a1',False),('b1',True),('b2',True),('a2',False)]:
 stem='tseng_fused_abba_'+label;native=stem+'_native_import';canonical=stem+'_canonical_reload';source_native='tseng_fused_capture_native_import' if fused else 'tseng_joint_native_import';source_canon='tseng_fused_capture_canonical_reload' if fused else 'tseng_joint_canonical_reload';tools=[]
 for kind,source,target in [('trial',source_native,native),('verify',source_native,native),('trial',source_canon,canonical),('verify',source_canon,canonical)]:
  name=kind+'_'+target+'.py';s=(root/'tools'/(kind+'_'+source+'.py')).read_text().replace(source_native,native).replace(source_canon,canonical);(root/'tools'/name).write_text(s);tools.append(name)
 runs.append({'label':label,'fused':fused,'native_directory':native+'_2026-10-06','canonical_directory':canonical+'_2026-10-06','tools':tools})
p={'runs':runs,'source_sha256':{name:sha(root/'tools'/name) for run in runs for name in run['tools']},'candidate_sha256':sha(root/'experiments/tseng_joint_transfer_2026-10-06/receipt.json'),'policy':'ABBA on fixed candidate with same physical/native FULL/STA/zero-fixup canonical reload checks. B first-analysis capture evidence reused; A separate capture analysis. No identity cache used.','scope':'Import+canonical stage comparison only; source staging/builds, fresh native reference/quality fallback and complete sequential lifecycle excluded.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[]
for run in runs:
 stages=[]
 for i,name in enumerate(run['tools']):
  t=time.monotonic();log=out/(run['label']+'_'+str(i)+'.log')
  with log.open('w') as stream:code=subprocess.run(['python3',str(root/'tools'/name)],cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
  stages.append({'tool':name,'exit_code':code,'wall_s':time.monotonic()-t,'log_sha256':sha(log)});assert code==0
 rows.append({**run,'stages':stages});print(run['label'],sum(s['wall_s'] for s in stages if s['tool'].startswith('trial_')),flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'runs':rows},indent=2)+'\n')
