"""Pointwise delayed-write memory relation, conditional on synchronous macro semantics."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'experiments/full_tags_pending_memory_relation_v1_2026-10-09'
D.mkdir(exist_ok=False)
Y=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys')
W=R/'experiments/full_ram_mapping_candidate_v1_2026-10-09/wrappers.v'
S=R/'experiments/full_tags_two_slice_relational_step_v1_2026-10-09/structural_binding.json'
# Arbitrary observation address proves pointwise equality, not sampled concrete words.
rtl='''module miter(input old_we,new_we,input [6:0] old_addr,new_addr,observe,
input [21:0] old_data,new_data,physical_word,output bad);
wire [21:0] logical_word=(old_we && old_addr==observe)?old_data:physical_word;
wire [21:0] logical_next=(new_we && new_addr==observe)?new_data:logical_word;
wire [21:0] physical_next=(old_we && old_addr==observe)?old_data:physical_word;
wire [21:0] related_next=(new_we && new_addr==observe)?new_data:physical_next;
assign bad=logical_next!=related_next;
endmodule
'''
(D/'miter.v').write_text(rtl)
# Intentionally omit committing old pending write. Must fail whenever old/new addresses differ.
(D/'mutation.v').write_text(rtl.replace('wire [21:0] physical_next=(old_we && old_addr==observe)?old_data:physical_word;','wire [21:0] physical_next=physical_word;'))
results={}
for name in ['miter','mutation']:
 script=f'read_verilog {name}.v\nhierarchy -check -top miter\nproc\nflatten\nopt\ncheck -assert\nsat -prove bad 0 -show-inputs -show-outputs -dump_json {name}_model.json\n'
 (D/f'{name}.ys').write_text(script)
 r=subprocess.run([str(Y),'-s',f'{name}.ys'],cwd=D,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
 (D/f'{name}.log').write_bytes(r.stdout)
 results[name]={'exit_code':r.returncode,'proof_success':b'no model found: SUCCESS' in r.stdout,'counterexample':b'model found: FAIL' in r.stdout}
assert results['miter']['exit_code']==0 and results['miter']['proof_success']
assert results['mutation']['exit_code']==0 and results['mutation']['counterexample'] and (D/'mutation_model.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out={'results':results,'bindings':{str(p):sha(p) for p in [Path(__file__),Y,W,S,*D.iterdir()] if p.is_file()},'relation':'L[a]=old_we && old_addr==a ? old_data : P[a]. P_next commits old pending; L_next commits current write; next pending becomes current write.','scope':'Binary abstract array pointwise induction for all seven-bit addresses and 22-bit data; physical macro synchronous write semantics and common slice pending controls are premises. Does not prove macro implementation, initial memory equality, native export or Full equivalence.','initial_obligation':'When pw=0, L=P is still an initial memory correspondence requirement, not a consequence of zero pw. Visible unreset output equality is separate.','functional_admission':False}
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(results))
