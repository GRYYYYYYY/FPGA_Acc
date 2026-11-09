"""Frozen whole-cohort bounded frontier repair ablation, unchanged base predictor."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from moved_history_repair_engine import repair_moved_history
root=Path(__file__).resolve().parents[1];base=root/'experiments/gf2_pressure_prediction_2026-10-06';r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');out=root/'experiments/gf2_pressure_frontier_repair_2026-10-06';out.mkdir();cases=[]
for row in r['rows']:
 w=row['data_width'];channels=row['channels'];d=base/f'gf2_d{w}_w{channels}';cases.append({'data_width':w,'channels':channels,'directory':str(d),'bindings':{str(p):sha(p) for p in (d/'receipt.json',d/'endpoints.json')}})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'sources_sha256':{n:sha(root/'tools'/n) for n in ('persistent_rc_context.py','moved_history_repair_engine.py','trial_gf2_pressure_frontier_repair.py')},'policy':'Existing moved-history residual capacity frontier wholeNET release, max4 repairs,1ns/10000labels, inherited history initiallyempty. Apply every failed case, keep failures; no fallback policy tuning.','scope':'Posthoc development repair ablation acrossall9cases; bounded completion not global routability classifier; whole-cohort native comparison afterrun.'},indent=2)+'\n');rows=[]
for c in cases:
 d=Path(c['directory']);prior=json.loads((d/'receipt.json').read_text());prior['history']={};t=time.monotonic();ctx=PersistentRCContext(d/'endpoints.json');setup=time.monotonic()-t;t=time.monotonic();result=repair_moved_history(ctx,prior);elapsed=time.monotonic()-t;dst=out/f"gf2_d{c['data_width']}_w{c['channels']}";dst.mkdir();(dst/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');row={'data_width':c['data_width'],'channels':c['channels'],'status':result['status'],'completed_connections':result['completed_connections'],'required_connections':result['required_connections'],'repairs':result['repairs'],'failure':result['failure'],'context_setup_s':setup,'repair_s':elapsed,'candidate_sha256':sha(dst/'receipt.json')};rows.append(row);assert all(sha(p)==h for p,h in c['bindings'].items());print(row,flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':len(rows)==9},indent=2)+'\n')
