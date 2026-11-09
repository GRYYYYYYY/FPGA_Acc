"""Time fresh native/canonical/quality acceptance for live-staged candidate."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_live_quality_pipeline_2026-10-06';out.mkdir();stages=[(prefix,'ex5p_live_staged_'+kind) for kind in ('native_import','canonical_reload','quality_gate') for prefix in ('trial','verify')];sources={prefix+'_'+name+'.py':sha(root/'tools'/(prefix+'_'+name+'.py')) for prefix,name in stages};candidate=root/'experiments/ex5p_live_staged_repair_2026-10-06/receipt.json';verification=candidate.parent/'verification.json';assert json.loads(verification.read_text())['receipt_sha256']==sha(candidate);reference=root/'experiments/ex5p_swapped_reference_canonical_reload_2026-10-06/receipt.json';p={'sources_sha256':sources,'candidate_sha256':sha(candidate),'reference_sha256':sha(reference),'stages':stages,'scope':'Fresh acceptance tail for staged candidate; candidate/front-end/context preparation already performed, reference canonical bundle archived. Not complete end-to-end latency or production commit.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[];start=time.monotonic()
for i,(prefix,name) in enumerate(stages):
 tool=prefix+'_'+name+'.py';log=out/(str(i)+'.log');begin=time.monotonic()
 with log.open('w') as stream:code=subprocess.run([sys.executable,str(root/'tools'/tool)],cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 rows.append({'tool':tool,'wall_s':time.monotonic()-begin,'exit_code':code,'log_sha256':sha(log)});print(tool,code,rows[-1]['wall_s'],flush=True)
 if code:break
r={'stages':rows,'wall_s':time.monotonic()-start,'complete':len(rows)==len(stages) and all(x['exit_code']==0 for x in rows),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
