"""Bind single-case six-audit evidence before native gate, no full-cohort claim."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_net_slack_focus_w8m0_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert len(r['rows'])==1 and (r['rows'][0]['width'],r['rows'][0]['index'])==(8,0);assert r['protocol_sha256']==sha(out/'protocol.json');p=json.loads((out/'protocol.json').read_text());assert all(sha(f)==h for f,h in p['sources'].items());file=out/'w8_m0/result.json';assert sha(file)==r['rows'][0]['result_sha256'];d=json.loads(file.read_text());assert d['result']['status']=='COMPLETE_CANDIDATE';audits={}
for name in ['control_timing_verification','physical_budget_verification','floor_verification','choice_verification','observation_verification','history_cost_verification']:
 f=file.parent/(name+'.json');a=json.loads(f.read_text());assert a['result_sha256']==sha(file);audits[name]=sha(f)
slack=ROOT/'experiments/mux_net_slack_budgets_2026-10-06';assert d['initial_budget_sha256']==sha(slack/'w8_m0.json') and d['initial_budget_verification_sha256']==sha(slack/'w8_m0_verification.json')
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),audits=audits,scope='Single focused w8m0 complete sketch and six-audit binding only. No full12outcome/nativeSTA or lifecyclegain claim.'),indent=2)+'\n');print('focused complete candidate audits bound')
