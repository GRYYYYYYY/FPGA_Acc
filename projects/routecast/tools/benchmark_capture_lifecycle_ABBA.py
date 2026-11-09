"""Fixed whole-family fresh ABBA block with independent snapshot audits."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/capture_lifecycle_ABBA_2026-10-06';out.mkdir();runs=[]
for i,mode in enumerate(['certified','fused','fused','certified']):
 old=f'gf2_{mode}_continuous_two_updates_2026-10-06';new=f'gf2_capture_ABBA{i}_{mode}_2026-10-06';trialold=f'trial_gf2_{mode}_continuous_two_updates.py';trialnew=f'trial_gf2_capture_ABBA{i}_{mode}.py';verifyold=f'verify_gf2_{mode}_continuous_two_updates.py';verifynew=f'verify_gf2_capture_ABBA{i}_{mode}.py'
 source=(root/'tools'/trialold).read_text().replace(old,new).replace(trialold,trialnew);(root/'tools'/trialnew).write_text(source)
 source=(root/'tools'/verifyold).read_text().replace(old,new);(root/'tools'/verifynew).write_text(source)
 stages=[trialnew,verifynew]
 if mode=='fused':
  name=f'verify_capture_ABBA{i}_provenance.py';(root/'tools'/name).write_text((root/'tools/verify_fused_capture_provenance.py').read_text().replace(old,new));stages.append(name)
 runs.append({'index':i,'mode':mode,'experiment':new,'stages':stages,'source_sha256':{n:sha(root/'tools'/n) for n in stages}})
(out/'protocol.json').write_text(json.dumps({'runs':runs,'source_sha256':sha(Path(__file__)),'order':'certified/fused/fused/certified','cases':[32,64,128],'updates_per_case':2,'scope':'One whole-family ABBA block, immutable matched policy/native/reference/quality trust chain. All runs retained, no stopping based on timing. Each pipeline measures context/stage/native tails/audits/certificate/selection/advance; sandbox setup and outer verification excluded. No cold-only comparator in this block, no statistical confidence or from-design gain.'},indent=2)+'\n');rows=[]
for run in runs:
 stages=[]
 for name in run['stages']:
  assert sha(root/'tools'/name)==run['source_sha256'][name];log=out/f'{run["index"]}_{name}.log';t=time.monotonic()
  with log.open('w') as f:process=subprocess.run(['python3',str(root/'tools'/name)],cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=900)
  stage={'name':name,'exit_code':process.returncode,'wall_s':time.monotonic()-t,'log_sha256':sha(log)};stages.append(stage);print(run['index'],run['mode'],stage,flush=True)
  if process.returncode:break
 base=root/'experiments'/run['experiment'];receipt=base/'receipt.json';row={'index':run['index'],'mode':run['mode'],'stages':stages,'complete':len(stages)==len(run['stages']) and all(x['exit_code']==0 for x in stages)}
 if receipt.exists():
  r=json.loads(receipt.read_text());row['receipt_sha256']=sha(receipt);row['case_wall_s']={str(c['width']):c['case_wall_s'] for c in r['rows']}
 rows.append(row);(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_runs_retained':len(rows)==4},indent=2)+'\n');print(row,flush=True)
