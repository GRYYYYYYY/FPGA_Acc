"""Bind complete paired lifecycles, compare all snapshots and report retained times."""
import json,statistics
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/capture_lifecycle_ABBA_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and r['all_runs_retained'] and len(r['rows'])==4;assert p['source_sha256']==sha(root/'tools/benchmark_capture_lifecycle_ABBA.py');times={m:{w:[] for w in ['32','64','128']} for m in ['certified','fused']};states={}
for run,row in zip(p['runs'],r['rows']):
 assert row['complete'] and row['index']==run['index'] and row['mode']==run['mode'];assert all(sha(root/'tools'/n)==h for n,h in run['source_sha256'].items());assert len(row['stages'])==len(run['stages'])
 for stage in row['stages']:assert stage['exit_code']==0 and sha(out/f'{run["index"]}_{stage["name"]}.log')==stage['log_sha256']
 base=root/'experiments'/run['experiment'];v=json.loads((base/'verification.json').read_text());receipt=json.loads((base/'receipt.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json')==row['receipt_sha256'];assert receipt['all_cases_retained'] and len(receipt['rows'])==3
 if run['mode']=='fused':assert json.loads((base/'capture_provenance_verification.json').read_text())['receipt_sha256']==row['receipt_sha256']
 for case in receipt['rows']:
  w=str(case['width']);assert case['complete'] and case['error'] is None and len(case['rounds'])==2;assert case['case_wall_s']==row['case_wall_s'][w];times[run['mode']][w].append(case['case_wall_s'])
  for revision in [1,2]:
   file=base/f'gf2_d{w}_accepted{revision}.json';assert sha(file)==case['rounds'][revision-1]['snapshot_sha256'];snapshot=json.loads(file.read_text());key=(w,revision)
   if key in states:assert states[key]==snapshot
   else:states[key]=snapshot
summary=[]
for w in ['32','64','128']:
 a=times['certified'][w];b=times['fused'][w];summary.append({'width':int(w),'certified_s':a,'fused_s':b,'certified_mean_s':statistics.mean(a),'fused_mean_s':statistics.mean(b),'fused_over_certified_mean':statistics.mean(b)/statistics.mean(a)})
result={'protocol_sha256':sha(out/'protocol.json'),'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'all24_snapshots_same_policy_state':True,'rows':summary,'scope':'Single ABBA block; all times retained. Measured lifecycle exclusions unchanged. No confidence interval, cold-only net benefit or broader family performance claim.'};(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
