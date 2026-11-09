import hashlib,itertools,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif';L=E/'full_source_export_startup_tag_write_trace_v21_2026-10-09/control.log'
lines=B.read_text().replace('\\\n',' ').splitlines();table=None
for i,line in enumerate(lines):
 t=line.split()
 if t and t[0]=='.names' and t[-1]=='b2015':
  rows=[]
  for s in lines[i+1:]:
   if s.lstrip().startswith('.'):break
   z=s.split()
   if z and not z[0].startswith('#'):rows.append(z)
  table={'inputs':t[1:-1],'rows':rows};break
assert table and len(table['inputs'])==5
V=E/'full_source_export_fixed_bus_replay_v19_2026-10-09/design.v';export=V.read_text();export_order=['b2014','new_n6607','new_n6618','b2016','b3121']
for i,n in enumerate(export_order):
 assert re.search(r'routing_segment_[^\n]*'+re.escape(n)+r'_output_0_0_to_lut_b2015_input_0_'+str(i),export)
permutation=[export_order.index(n) for n in table['inputs']]
polarity={r[-1] for r in table['rows']};assert len(polarity)==1

def evaluate(vals):
 vals=[vals[i] for i in permutation]
 answers=set()
 for a in itertools.product(*[('0','1') if v=='x' else (v,) for v in vals]):
  covered=any(all(p=='-' or p==v for p,v in zip(r[0],a)) for r in table['rows']);answers.add(str(int(covered)) if polarity=={'1'} else str(int(not covered)))
 return next(iter(answers)) if len(answers)==1 else 'x'
records=[]
for line in L.read_text().splitlines():
 if 'COUNTER_CONTROL cycle=' not in line:continue
 cycle=int(re.search(r'cycle=\s*(\d+)',line)[1])
 if cycle>5:continue
 vals=re.search(r'exp_Dinputs=([01x]+)',line)[1];observed=re.search(r'exp_highD=([01x])',line)[1];assert evaluate(vals)==observed
 interventions=[]
 for i,v in enumerate(vals):
  if v!='x':continue
  for forced in '01':
   altered=list(vals);altered[i]=forced;interventions.append({'input_index':i,'actual_net':export_order[i],'forced_value':forced,'output':evaluate(altered)})
 records.append({'cycle':cycle,'actual_inputs':vals,'actual_output':observed,'single_input_interventions':interventions})
assert len(records)==6
out={'export_input_order':export_order,'blif_input_permutation':permutation,'table':table,'observations':records,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [B,L,V]},'scope':'Exact exported LUT consensus and existing post-edge D observations, with single-input interventions. Does not identify pre-edge source guard values or prove counterfactual reachability or all mismatch causality.'}
d=E/'full_flush_high_d_unknown_sensitivity_v1_2026-10-09';d.mkdir(exist_ok=True);(d/'sensitivity_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out['table']));print(json.dumps(records[3],indent=2))
