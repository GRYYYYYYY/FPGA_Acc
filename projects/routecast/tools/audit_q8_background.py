"""Exact Fraction replay of Q8 background history; no route label input."""
from fractions import Fraction
from pathlib import Path
import json
from pre_route_endpoints import sha
parent=Path('experiments/q8_pressure_rounds_2026-10-04');out=Path('experiments/q8_pressure_evaluation_2026-10-04');p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());rows=[]
for name,paths in p['inputs'].items():
    initial=json.loads(Path(paths['background_prediction']['path']).read_text())['node_occupancy'];exact={n:Fraction(v) for n,v in initial.items()};observed=json.loads(Path(p['round1'][name]['path']).read_text())['node_occupancy']
    for round_id in (2,3):
        f=parent/f'{name}_round{round_id}_background.json';assert sha(f)==r['artifacts'][f.name];actual=json.loads(f.read_text());exact={n:(exact.get(n,0)+observed.get(n,0))/2 for n in set(exact)|set(observed)};keys=set(exact)|set(actual);error=sum((abs(Fraction(actual.get(n,0),256)-exact.get(n,0)) for n in keys),Fraction(0));assert error==0
        rows.append({'design':name,'round':round_id,'all_rr_background_l1_quantization_error':[error.numerator,error.denominator],'exact_half_history_matches':True,'background_positive_while_latest_prediction_unused':sum(v>0 and observed.get(n,0)==0 for n,v in actual.items()),'scope':'all RR node backgrounds; positive unused demand can be legitimate half-decaying memory, not proof of sticky rounding'})
        observed=json.loads((parent/f'{name}_round{round_id}.json').read_text())['node_occupancy']
(out/'exact_background_audit.json').write_text(json.dumps({'auditor_sha256':sha(__file__),'rows':rows,'all_checks_passed':True},indent=2)+'\n');print(json.dumps(rows))
