"""Actual BLIF ready control dependency and early observed export masking."""
import json,hashlib,itertools
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_ready_csr_dependency_v1_2026-10-09';D.mkdir(exist_ok=True)
B=R/'experiments/full_ram_init_export_runtime_v8_2026-10-09/design.blif';ls=B.read_text().splitlines();nodes={}
for i,l in enumerate(ls):
 if not l.startswith('.names '):continue
 rows=[]
 for t in ls[i+1:]:
  if t.startswith('.'):break
  if t.strip():rows.append(t.split())
 nodes[l.split()[-1]]={'inputs':l.split()[1:-1],'rows':rows}
def val(n,v):
 c=nodes[n];pol=int(c['rows'][0][1]);hit=any(all(p=='-' or p==str(v[b]) for p,b in zip(pattern,c['inputs'])) for pattern,_ in c['rows']);return pol if hit else 1-pol
names=sorted(set(nodes['new_n6108']['inputs']+nodes['new_n5937']['inputs']+nodes['new_n5366']['inputs']))
checked=0
for bits in itertools.product([0,1],repeat=len(names)):
 v=dict(zip(names,bits));v['new_n5366']=val('new_n5366',v)
 assert val('new_n6108',v)==val('new_n5937',v);checked+=1
A=R/'experiments/full_ibus_ready_export_lut_v1_2026-10-09/audit.json';mask=json.loads(A.read_text())['records'][0]['mask']
def consensus(pins):
 vs={mask[-1-sum(int(b)<<i for i,b in enumerate(bs))] for bs in itertools.product(*[['0','1'] if b=='x' else [b] for b in pins])};return next(iter(vs)) if len(vs)==1 else 'x'
for control,tag in itertools.product('01x',repeat=2):assert consensus(['0',control,'0','1',tag])==control
T=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09/trace_audit.json';a=json.loads(T.read_text());selected=[]
for r in a['rows']:
 p=r['native_ready_pins'][::-1]
 if p[0]=='0' and p[2:4]=='01':assert r['native_ready']==p[1];selected.append(r['cycle'])
out={'nodes':{n:nodes[n] for n in ['b2692','new_n6085','new_n6108','new_n5937','new_n5366']},'capture_binary_equivalence_rows':checked,'export_early_mask_ternary_cases':9,'actual_matching_cycles':selected,'first_difference':a['first_difference'],'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [B,A,T]},'scope':'Actual export ready equals node6085 for135observed masked contexts, independent of tag error; node6085 AND includes6108, which is binary-equivalent to earlier CSRcapture5937. No observed6108 trace or complete unknown propagation/cause claim; need actual additional node inputs.'}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'capture_binary_rows':checked,'actual_masked_cycles':len(selected),'scope':out['scope']},indent=2))
