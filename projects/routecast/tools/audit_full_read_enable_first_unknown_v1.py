"""Existing actual exported first-unknown LUT input propagation, no new stimulus."""
import hashlib,itertools,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';V=E/'full_ram_init_export_runtime_v8_2026-10-09/VexRiscvFull_post_synthesis.v';L=E/'full_source_export_startup_tag_write_trace_v21_2026-10-09/control.log';B=E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif';v=V.read_text();log=L.read_text();edges={}
for src,dst in re.findall(r'\.datain\(\\(\S+)\s*\)\s*,\s*\.dataout\(\\(\S+)\s*\)',v):edges[dst]=src
records=[]
def table(node):
 pattern=r'LUT_K\s*#\(\s*\.K\((\d+)\),\s*\.LUT_MASK\((\d+)\x27b([01]+)\)\s*\)\s*\\lut_'+re.escape(node)+r'\s*\('
 match=re.search(pattern,v);assert match;K=int(match[1]);assert int(match[2])==2**K and len(match[3])==2**K
 return K,match[3]
def evaluate(mask,values):
 choices=[('0','1') if c in 'xz' else (c,) for c in values];outputs={mask[-1-sum(int(c)<<i for i,c in enumerate(bits))] for bits in itertools.product(*choices)}
 return next(iter(outputs)) if len(outputs)==1 else 'x'
for node,prefix in [('b2692','READ_CONTROL'),('new_n6085','FLUSH_CONTROL')]:
 K,mask=table(node);sources=[edges['lut_'+node+'_input_0_'+str(i)] for i in range(K)];rows=[]
 for m in re.finditer(prefix+r' cycle=\s*(\d+) exp_inputs=([01xz]+)',log):
  cycle=int(m[1]);vals=m[2];assert len(vals)==K
  if cycle<=6:rows.append({'cycle':cycle,'inputs':vals,'consensus_output':evaluate(mask,vals)})
 records.append({'node':node,'K':K,'mask':mask,'ordered_actual_sources':sources,'observations':rows})
re_node,flush_node=records;assert re_node['ordered_actual_sources'][1]=='lut_new_n6085_output_0_0';assert flush_node['ordered_actual_sources'][3]=='lut_new_n6108_output_0_0'
assert re_node['observations'][3]['consensus_output']=='0' and re_node['observations'][4]['consensus_output']=='x';assert flush_node['observations'][3]['consensus_output']=='0' and flush_node['observations'][4]['consensus_output']=='x'
values=re_node['observations'][4]['inputs'];counterfactuals={b:evaluate(re_node['mask'],values[:1]+b+values[2:]) for b in '01'};assert counterfactuals=={'0':'0','1':'1'}
out={'records':records,'cycle4_counterfactual_new_n6085':counterfactuals,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [V,L,B]},'conclusion':'Existing cycle4 input observations and exact exported LUT masks support new_n6108=X => new_n6085=X => b2692=X locally. Known decode-valid zero makes tag-error X irrelevant to this immediate read-enable function.','scope':'Local observed input/mask propagation, not origin of new_n6108 X or causal explanation of all Full mismatches. Postedge observations cannot establish same-edge active-region ordering.'};D=E/'full_read_enable_first_unknown_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'first_unknown_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'propagation_checked':True,'cycle4_counterfactuals':counterfactuals},indent=2))
