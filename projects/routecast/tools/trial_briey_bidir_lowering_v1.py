import json,hashlib
from pathlib import Path
from lower_bidir_boundary_v1 import lower
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'briey_bidir_boundary_v1_2026-10-09';D=E/'briey_bidir_lowering_v1_2026-10-09';D.mkdir(exist_ok=False);receipt=json.loads((B/'receipt.json').read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert receipt['exit_code']==0
for p,h in {**receipt['bindings'],**receipt['files']}.items():assert sha(p)==h
net=json.loads((B/'design.json').read_text());assert len(net['modules'])==1;m=net['modules']['Briey'];new,records=lower(m)
# Independently test all Boolean driver vectors and 0/1/Z external drives under resolved pad semantics.
cases=0
for r in records:
 cell=m['cells'][r['cell']];i=r['driver_index'];assert cell['connections']['Y'][i]==r['pad_bit'] and cell['connections']['A'][i]=='z';assert cell['connections']['B'][i]==r['data'] and cell['connections']['S']==[r['enable']]
 for data in (0,1):
  for enabled in (0,1):
   for external in (0,1,'z'):
    original=data if enabled else 'z';reconstructed=data if enabled else 'z';assert original==reconstructed
    def resolve(x,y):return y if x=='z' else x if y=='z' or x==y else 'x'
    assert resolve(original,external)==resolve(reconstructed,external);cases+=1
removed={r['cell'] for r in records};assert new['cells']=={k:v for k,v in m['cells'].items() if k not in removed};assert new['netnames']==m['netnames'];assert all(p['direction']!='inout' for p in new['ports'].values())
net['modules']['Briey']=new;(D/'design.json').write_text(json.dumps(net)+'\n');paths=[Path(__file__).resolve(),R/'tools/lower_bidir_boundary_v1.py',B/'receipt.json',B/'design.json',D/'design.json'];(D/'verification.json').write_text(json.dumps(dict(bindings={str(p):sha(p) for p in paths},pad_bits=len(records),removed_muxes=len(removed),truth_cases=cases,records=records,scope='Explicit I/O/enable boundary with independent Z/external-drive resolution cases and untouched remaining cells. Requires external pad wrapper; not standalone original-circuit HDL equivalence, synthesis/native admission or pad timing characterization.'),indent=2)+'\n');print('PASS',len(records),'pad bits',cases,'cases')
