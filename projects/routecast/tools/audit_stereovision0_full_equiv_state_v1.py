"""Complete exported equiv cells and remaining top-output obligations."""
import json,re
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/diffeq2_stereo0_full_equivalence_alternative_v1_2026-10-10/stereovision0';p=S/'receipt.json';v=json.loads(p.read_text());assert v['exit_code']==1 and not v['all_equiv_cells_proven_log'];assert all(sha(k)==h for k,h in v['bindings'].items());jp=S/'pre_induction_equiv.json';m=json.loads(jp.read_text())['modules']['equiv'];outputs={bit for d in m['ports'].values() if d['direction']=='output' for bit in d['bits']};rows=[]
for name,c in m['cells'].items():
 if c['type']!='$equiv':continue
 conn=c['connections'];assert set(conn)=={'A','B','Y'} and all(len(x)==1 for x in conn.values());rows.append(dict(cell=name,A=conn['A'][0],B=conn['B'][0],Y=conn['Y'][0],proven=conn['A']==conn['B'],top_output=conn['Y'][0] in outputs))
assert len(rows)==21619;pending=[x for x in rows if not x['proven']];assert len(pending)==1746
text=(S/'equivalence.log').read_text();assert "ERROR: Found 1746 unproven $equiv cells" in text
D=R/'experiments/stereovision0_full_equiv_state_v1_2026-10-10';assert not D.exists();D.mkdir();bindings={str(x):sha(x) for x in [Path(__file__).resolve(),p,jp,S/'equivalence.log']};(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,all21619_equiv_cells=rows,unproved_count=len(pending),unproved_top_output_count=sum(x['top_output'] for x in pending),all_unproved_top_output_cells=[x for x in pending if x['top_output']],scope='All exported pre-induction equiv cells directly audited. A==B records proved obligation; original source correspondence/fullstartup semantics not inferred. Final log still1746unproved. No cell/point omission or native/family admission.'),indent=2)+'\n');print('all',len(rows),'pending',len(pending),'pending top outputs',sum(x['top_output'] for x in pending))
