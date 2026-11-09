"""Actual exported capture6108 mask evaluated from retained full operand preedges."""
import json,itertools,hashlib,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_capture_existing_trace_v1_2026-10-09';D.mkdir(exist_ok=True)
A=R/'experiments/full_csr_capture_operands_trace_v1_2026-10-09/trace_audit.json';B=R/'experiments/full_ibus_ready_control_export_luts_v1_2026-10-09/audit.json';T=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09/trace_audit.json'
a=json.loads(A.read_text());rec=next(r for r in json.loads(B.read_text())['records'] if r['node']=='new_n6108');t=json.loads(T.read_text());rows=[]
assert len(a['rows'])==len(t['rows'])==512 and t['replay_fidelity'] and a['replay_fidelity']
for r,ready in zip(a['rows'],t['rows']):
 assert r['cycle']==ready['cycle']
 pins=[r[p['node']] for p in rec['input_routes_lsb_first']];values={rec['mask'][-1-sum(int(b)<<i for i,b in enumerate(bs))] for bs in itertools.product(*[['0','1'] if b.lower() in ['x','z'] else [b] for b in pins])};value=next(iter(values)) if len(values)==1 else 'x'
 rows.append({'cycle':r['cycle'],'computed_6108':value,'observed_5937':r['new_n5937'],'observed_6085':ready['native_ready_pins'][::-1][1],'observed_ready':ready['native_ready'],'matches_5937':value==r['new_n5937']})
assert all(r['matches_5937'] for r in rows)
control=next(r for r in json.loads(B.read_text())['records'] if r['node']=='new_n6085')
# Counterfactual local masking: capture0 forces control0 for every ternary other pin.
checks=0
for other in itertools.product('01x',repeat=4):
 pins=list(other[:3])+['0',other[3]]
 vals={control['mask'][-1-sum(int(b)<<i for i,b in enumerate(bs))] for bs in itertools.product(*[['0','1'] if b=='x' else [b] for b in pins])}
 assert vals=={'0'};checks+=1
out={'capture_zero_masks_control_ternary_cases':checks,'cycles':512,'matches_capture5937':512,'computed6108_counts':dict(collections.Counter(r['computed_6108'] for r in rows)),'early_rows':rows[:7],'rows':rows,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [A,B,T]},'scope':'Actual export6108 mask and routes evaluated from existing512operand preedges with frozenfullreplay preserved. Values match observed5937 allcycles; not direct6108probe, nor evidence that other6085inputs do not mask it. Early counter-high/5938 chain separately traced.'}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','hashes']},indent=2))
