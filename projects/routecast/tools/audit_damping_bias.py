"""Quantify integer upward-rounding, not a causal accuracy claim."""
import json
from pathlib import Path
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
parent=Path('experiments/damped_pressure_rounds_2026-10-04');out=Path('experiments/damped_pressure_evaluation_2026-10-04');p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());rows=[]
for name,paths in p['inputs'].items():
    g=read_rr_graph(paths['graph']['path']);channels={n for n,v in g.nodes.items() if v.type in {'CHANX','CHANY'}}
    old={int(n):v for n,v in json.loads(Path(paths['background_prediction']['path']).read_text())['node_occupancy'].items()};observed={int(n):v for n,v in json.loads(Path(p['round1'][name]['path']).read_text())['node_occupancy'].items()}
    for round_id in (2,3):
        f=parent/f'{name}_round{round_id}_background.json';assert sha(f)==r['artifacts'][f.name];current={int(n):v for n,v in json.loads(f.read_text()).items()};union=set(old)|set(observed)
        assert current=={n:(old.get(n,0)+observed.get(n,0)+1)//2 for n in union if old.get(n,0)+observed.get(n,0)>0}
        rows.append({'design':name,'round':round_id,'channel_background_nonzero':sum(n in channels for n in current),'channel_currently_unused_but_background_positive':sum(n in channels and observed.get(n,0)==0 for n in current),'channel_sticky_unit_cases':sum(n in channels and old.get(n,0)==1 and observed.get(n,0)==0 for n in union),'channel_rounding_excess_half_units':sum((old.get(n,0)+observed.get(n,0))%2 for n in union if n in channels),'scope':'excess measured against exact half average of the integer prior state and current prediction, not ideal whole-history exponential average'})
        old=current;observed={int(n):v for n,v in json.loads((parent/f'{name}_round{round_id}.json').read_text())['node_occupancy'].items()}
(out/'rounding_bias.json').write_text(json.dumps({'auditor_sha256':sha(__file__),'rows':rows,'conclusion':'upward rounding retains demand on unused channels; observed accuracy loss not proven solely caused by rounding'},indent=2)+'\n');print(json.dumps(rows))
