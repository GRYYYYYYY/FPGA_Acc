"""Inventory actual asynchronous reset pins against the frozen replay stimulus."""
import collections
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
E=R/'experiments'
files=[E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json',E/'full_source_structural_initial_obligations_v1_2026-10-09/initial_obligations.json',E/'full_source_export_fixed_bus_replay_v19_2026-10-09/frozen_bus_trace.json',E/'full_source_export_fixed_bus_replay_v19_2026-10-09/tb.v']
m=max(json.loads(files[0].read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})))
drivers={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs}
inputs={b:n for n,p in m['ports'].items() if p['direction']=='input' for b in p['bits']}
records=[]
for r in json.loads(files[1].read_text())['registers']:
 if r['reset_kind']!='asynchronous_reset':continue
 n,c=drivers[r['source_bit']];b=c['connections']['ARST'][0]
 records.append({'source_bit':r['source_bit'],'cell':n,'ARST_bit':b,'top_input':inputs.get(b),'ARST_polarity':c['parameters']['ARST_POLARITY'],'reset_value':r['reset_values']['ARST']})
rows=json.loads(files[2].read_text())['rows'];schedule=[{k:r[k] for k in ['cycle','reset','debugReset']} for r in rows[:4]]
assert len(records)==115
counts=dict(collections.Counter(r['top_input'] for r in records));assert counts=={'reset':108,'debugReset':7}
assert all(int(r['ARST_polarity'],2)==1 for r in records)
assert all(r['reset']==r['debugReset']==('1' if i<3 else '0') for i,r in enumerate(schedule))
tb=files[3].read_text();assert 'reset=1;debugReset=1;' in tb
out={'paired_async_register_bits':len(records),'direct_top_reset_counts':counts,'first_four_frozen_cycles':schedule,'records':records,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'scope':'Actual source reset pin inventory and frozen stimulus only. Both reset pins are asserted at startup; debugReset is not omitted. Does not establish all mapped/native reset event correspondence, unknown-edge behavior, RAM initialization, or global Full equivalence.'}
d=E/'full_source_async_reset_stimulus_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'stimulus_audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['records','hashes']},indent=2))
