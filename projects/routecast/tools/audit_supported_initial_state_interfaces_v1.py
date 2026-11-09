"""Complete top ports, sequential controls and init annotations for all eight designs."""
import json,re
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];fp=R/'experiments/verilog_frontend_cohort_full_audit_v1_2026-10-10/verification.json';f=json.loads(fp.read_text());assert all(sha(k)==h for k,h in f['bindings'].items());sp=R/'experiments/verilog_supported_structural_cohort_v1_2026-10-10/receipt.json';s=json.loads(sp.read_text());names=[x['name'] for x in s['rows']];tops={x['name']:x['top'] for x in f['rows']};bindings={str(x):sha(x) for x in [Path(__file__).resolve(),fp,sp]};rows=[]
for name in names:
 directory={'sha':'sha1_frontend_readiness_v1_2026-10-10','blob_merge':'blob_merge_frontend_readiness_v1_2026-10-10'}.get(name,'verilog_frontend_cohort_v3_2026-10-10/'+name);S=R/'experiments'/directory;p=S/'receipt.json';r=json.loads(p.read_text());assert r['exit_code']==0 and all(sha(k)==h for k,h in r['bindings'].items());jp=S/'design.json';m=json.loads(jp.read_text())['modules'][tops[name]];bindings.update({str(x):sha(x) for x in [p,jp]});controls=Counter();ff=Counter();qinit=Counter();initial={};conflicts=[]
 for net,d in m['netnames'].items():
  if 'init' in d['attributes']:
   assert len(d['bits'])==len(d['attributes']['init'])
   for bit,value in zip(d['bits'],d['attributes']['init'][::-1]):initial.setdefault(bit,set()).add(value)
 for c in m['cells'].values():
  if not c['type'].startswith('$_DFF_'):continue
  ff[c['type']]+=1
  for pin in ['C','R']:
   if pin in c['connections']:controls[(pin,tuple(c['connections'][pin]))]+=1
  for q in c['connections']['Q']:qinit[''.join(sorted(initial.get(q,[]))) or 'unannotated']+=1
 rows.append(dict(name=name,top=tops[name],all_top_ports=m['ports'],reset_named_input_candidates=[n for n,d in m['ports'].items() if d['direction']=='input' and re.search('reset|rst',n,re.I)],sequential_types=dict(ff),all_clock_reset_control_counts=[dict(pin=k[0],bits=list(k[1]),count=v) for k,v in controls.items()],all_q_initial_annotation_sets=dict(qinit),concrete_init_collision_bits=[q for q,v in initial.items() if {'0','1'}<=v]))
D=R/'experiments/supported_initial_state_interfaces_v1_2026-10-10';assert not D.exists();D.mkdir();(D/'audit.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='All8 complete archived JSON ports, every DFF control/Q init set. Reset name heuristic is not actual reset existence/behavior proof; clocks not assumed single, uninitialized states not forced zero. No startup synchronization, original-source temporal/native/family admission.'),indent=2)+'\n');print([(x['name'],x['sequential_types'],x['reset_named_input_candidates'],x['all_q_initial_annotation_sets']) for x in rows])
