"""All original BLIF flops, pins and init constraints; separate from strict oracle."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/verilog_frontend_cohort_v3_2026-10-10/arm_core';rp=S/'receipt.json';r=json.loads(rp.read_text());assert r['exit_code']==0 and all(sha(k)==v for k,v in r['bindings'].items());jp=S/'design.json';bp=S/'design.blif';m=json.loads(jp.read_text())['modules']['arm_core'];names={'$false':'0','$true':'1','$undef':'x'};init=defaultdict(set)
for name,d in m['netnames'].items():
 bits=d['bits'];offset=d.get('offset',0);upto=d.get('upto',0)
 for i,bit in enumerate(bits):
  wire=name if len(bits)==1 and offset==0 and not upto else f'{name}[{offset+(len(bits)-1-i if upto else i)}]'
  if wire in names:assert names[wire]==bit
  names[wire]=bit
 if 'init' in d['attributes']:
  assert len(d['attributes']['init'])==len(bits)
  for bit,v in zip(bits,d['attributes']['init'][::-1]):init[bit].add(v)
expected=Counter()
for c in m['cells'].values():
 if c['type']=='$_DFF_P_':expected[(c['connections']['D'][0],c['connections']['Q'][0],c['connections']['C'][0])]+=1
actual=Counter();violations=[];mixed=[];distribution=Counter()
with bp.open() as stream:
 for line in stream:
  if not line.startswith('.latch '):continue
  t=line.split();assert len(t)==6 and t[3]=='re';d,q,clk=[names[t[i]] for i in (1,2,4)];v={'0':'0','1':'1','2':'x','3':'x'}[t[5]];actual[(d,q,clk)]+=1;distribution[v]+=1
  defined=init[q]&{'0','1'}
  if len(defined)>1 or (defined and v not in defined):violations.append(dict(q=q,wire=t[2],json_values=sorted(init[q]),blif_value=v))
  if 'x' in init[q] and defined:mixed.append(dict(q=q,wire=t[2],json_values=sorted(init[q]),blif_value=v))
D=R/'experiments/arm_core_blif_initialization_v1_2026-10-10';assert not D.exists();D.mkdir();bindings={str(p):sha(p) for p in [Path(__file__).resolve(),rp,jp,bp]}
(D/'audit.json').write_text(json.dumps(dict(bindings=bindings,json_dff_count=sum(expected.values()),blif_dff_count=sum(actual.values()),all_d_q_clock_multisets_exact=expected==actual,blif_initialization_distribution=dict(distribution),defined_initialization_violation_count=len(violations),violations=violations,mixed_unknown_defined_flops=mixed,scope='Complete original JSON/BLIF DFF_P pin multiset and defined-init constraint check only. Unknown treated as no concrete constraint in this separate diagnostic, not alteration of strict original structural oracle. Does not prove gate truth tables, source initial correspondence or native/family admission.'),indent=2)+'\n');print(json.dumps(dict(ff=sum(actual.values()),pin_multisets_equal=expected==actual,defined_init_violations=len(violations),mixed_flops=len(mixed),distribution=dict(distribution))))
