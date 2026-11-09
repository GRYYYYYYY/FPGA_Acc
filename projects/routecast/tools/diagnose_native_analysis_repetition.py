"""Classify authenticated native search versus analysis and capture evidence."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments/gf2_certified_continuous_two_updates_2026-10-06';p=json.loads((base/'protocol.json').read_text());r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');out=root/'experiments/gf2_native_analysis_repetition_2026-10-06';out.mkdir(exist_ok=True);rows=[]
for case in p['cases']:
 for rd in case['rounds']:
  sandbox=Path(rd['sandbox']);stages=[]
  for name in rd['stages']:
   if not name.startswith('trial_'):continue
   parent=sandbox/'experiments'/(name.removeprefix('trial_').removesuffix('.py')+'_2026-10-06');receipt=parent/'receipt.json';q=json.loads(receipt.read_text());verification=json.loads((parent/'verification.json').read_text());assert verification['receipt_sha256']==sha(receipt)
   if 'results' in q:
    cmd=q['results'][0]['reload_command'];assert '--analysis' in cmd and '--route' not in cmd;mode='CANONICAL_FULL_ANALYSIS';logs=[Path(f) for f in q['results'][0]['sha256'] if Path(f).name in ['capture.log','identity.log','reload.log']];assert len(logs)==3
   else:
    cmd=q.get('command') or json.loads((parent/'protocol.json').read_text())['command'];mode='COLD_ROUTE_SEARCH' if '--route' in cmd else 'CANDIDATE_FULL_ANALYSIS';assert ('--route' in cmd)!=('--analysis' in cmd);logs=[Path(f) for f in q['files_sha256'] if Path(f).suffix=='.log']
   stages.append({'stage':name,'mode':mode,'command':cmd,'receipt_sha256':sha(receipt),'logs':{str(f):sha(f) for f in logs}})
  rows.append({'width':case['width'],'target':rd['target'],'stages':stages})
(out/'receipt.json').write_text(json.dumps({'lifecycle_receipt_sha256':sha(base/'receipt.json'),'source_sha256':sha(Path(__file__)),'rows':rows,'scope':'Native command modes from authenticated stage receipts and canonical capture/identity/reload logs. Parent childprocess walls include parsing/serialization/setup, not route-search CPUtime. Canonical stage three invocations; candidateimport initialidentity+analysis. No removed checks or performance claim.'},indent=2)+'\n');print({'rounds':len(rows),'classified_trial_stages':sum(len(x['stages']) for x in rows),'cold_route_search_stages':sum(s['mode']=='COLD_ROUTE_SEARCH' for x in rows for s in x['stages']),'candidate_analysis_stages':sum(s['mode']=='CANDIDATE_FULL_ANALYSIS' for x in rows for s in x['stages']),'canonical_analysis_stages':sum(s['mode']=='CANONICAL_FULL_ANALYSIS' for x in rows for s in x['stages'])})
