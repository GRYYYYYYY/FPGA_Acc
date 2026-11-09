"""Percomplete candidate proof binding without a mutable wholecohort receipt dependency."""
import json,sys
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];w,i=map(int,sys.argv[1:]);out=ROOT/'experiments/mux_owned_bound_cache_cohort_2026-10-06';file=out/f'w{w}_m{i}/result.json';d=json.loads(file.read_text());p=json.loads((out/'protocol.json').read_text());assert all(sha(f)==h for f,h in p['sources'].items());assert d['result']['status']=='COMPLETE_CANDIDATE' and d['result']['candidate']['failure'] is None;audits={}
for name in ['control_timing_verification','physical_budget_verification','floor_verification','choice_verification','observation_verification','history_cost_verification']:
 f=file.parent/(name+'.json');a=json.loads(f.read_text());assert a['result_sha256']==sha(file);audits[name]=sha(f)
slack=ROOT/'experiments/mux_net_slack_budgets_2026-10-06';assert d['initial_budget_sha256']==sha(slack/f'w{w}_m{i}.json') and d['initial_budget_verification_sha256']==sha(slack/f'w{w}_m{i}_verification.json')
(file.parent/'native_input_verification.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),result_sha256=sha(file),verifier_sha256=sha(Path(__file__)),audits=audits,scope='This complete candidate six-audit/protocol/budget proof binding only. Othercases pending; nativequality proof separate.'),indent=2)+'\n');print('native input bound',w,i)
