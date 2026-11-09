"""Disjoint outer-stage cost accounting; nested model/native clocks never added."""
import json,sys
from decimal import Decimal
from pathlib import Path
from pre_route_endpoints import sha
D=Path(sys.argv[1]).resolve();proof=json.loads((D/'verification.json').read_text());assert proof['all_cases_both_complete_arms_authenticated'] and all(sha(p)==h for p,h in proof['bindings'].items());r=json.loads((D/'receipt.json').read_text());stages=json.loads((D/'stages.json').read_text());rows=[];byarm={}
for arm in ['cold','seed']:
 selected=[x for x in stages if x.get('arm')==arm or ('log' in x and Path(x['log']).is_relative_to(D/arm))];assert selected and all(x.get('exit_code',0)==0 for x in selected)
 total=Decimal(str(next(x for x in r['rows'] if x['arm']==arm)['continuous_arm_seconds']));measured=sum((Decimal(str(x['seconds'])) for x in selected),Decimal(0));outside=total-measured;assert outside>=0
 categories={}
 for x in selected:
  key=Path(x['log']).name if 'log' in x else x['stage'];assert key not in categories;categories[key]=str(Decimal(str(x['seconds'])))
 row=dict(arm=arm,continuous_seconds=str(total),disjoint_outer_stage_seconds=str(measured),between_stage_and_authentication_seconds=str(outside),outer_stages=categories);rows.append(row);byarm[arm]=(total,categories)
cold=byarm['cold'][0];seed,categories=byarm['seed'];handoff=Decimal(categories['sha1_model_native_seed.log']);remaining=seed-handoff;threshold=cold-remaining
inputs=[Path(__file__).resolve(),D/'verification.json',D/'receipt.json',D/'stages.json'];(D/'cost_envelope.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in inputs},rows=rows,seed_handoff_model_audits_native_driver_seconds=str(handoff),seed_other_paid_seconds=str(remaining),required_handoff_driver_seconds_below_at_fixed_other_costs=str(threshold),even_zero_driver_insufficient_at_fixed_other_costs=threshold<=0,scope='Observed single trial outer sequential stages partition continuous clocks. Driver contains model/serialization/full model audits/same native seed route; no nested clock double counting. Fixed-other-cost threshold is arithmetic diagnostic, not permission to remove audits, not a measured alternative or a replicated speedup.'),indent=2)+'\n');print('COST ENVELOPE',str(handoff),str(remaining),str(threshold))
