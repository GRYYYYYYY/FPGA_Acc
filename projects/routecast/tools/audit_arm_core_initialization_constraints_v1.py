"""Complete init annotation constraint inventory, not an oracle waiver."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/verilog_frontend_cohort_v3_2026-10-10/arm_core';rp=S/'receipt.json';r=json.loads(rp.read_text());assert r['exit_code']==0 and all(sha(k)==v for k,v in r['bindings'].items());jp=S/'design.json';m=json.loads(jp.read_text())['modules']['arm_core'];a=defaultdict(list);counts=Counter()
for name,d in m['netnames'].items():
 if 'init' not in d['attributes']:continue
 init=d['attributes']['init'];assert len(init)==len(d['bits'])
 for i,(bit,v) in enumerate(zip(d['bits'],init[::-1])):
  assert v in '01x';a[bit].append(dict(netname=name,index=i,value=v));counts[v]+=1
concrete_conflicts=[];mixed=[]
for bit,annotations in a.items():
 values={x['value'] for x in annotations}
 if {'0','1'}<=values:concrete_conflicts.append(dict(bit=bit,annotations=annotations))
 if 'x' in values and values&{'0','1'}:mixed.append(dict(bit=bit,annotations=annotations))
ff=Counter();qbits=set()
for c in m['cells'].values():
 if c['type']!='$_DFF_P_':continue
 q=c['connections']['Q'];assert len(q)==1;q=q[0];qbits.add(q);values={x['value'] for x in a.get(q,[])}
 ff['no_annotation' if not values else ''.join(sorted(values))]+=1
D=R/'experiments/arm_core_initialization_constraints_v1_2026-10-10';assert not D.exists();D.mkdir();bindings={str(Path(__file__).resolve()):sha(Path(__file__)),str(rp):sha(rp),str(jp):sha(jp)}
(D/'audit.json').write_text(json.dumps(dict(bindings=bindings,annotation_counts=dict(counts),annotated_unique_bits=len(a),concrete_conflict_count=len(concrete_conflicts),concrete_conflicts=concrete_conflicts,mixed_unknown_defined_unique_bit_count=len(mixed),mixed_unknown_defined=mixed,dff_annotation_value_sets=dict(ff),dff_unique_qbits=len(qbits),scope='All original JSON netname init annotations and all DFF_P Q annotation sets. Concrete 0/1 collisions distinguished from x/defined sets without changing strict structural oracle. No BLIF or temporal correspondence proof, no source/native/family admission.'),indent=2)+'\n');print(json.dumps(dict(annotation_counts=dict(counts),concrete_conflicts=len(concrete_conflicts),mixed_unique_bits=len(mixed),dff_sets=dict(ff))))
