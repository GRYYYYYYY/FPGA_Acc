"""Abstract whole-word versus independently resolved lane collision read choices."""
import json,hashlib,subprocess,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'cross_read_word_coherence_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);m=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(m['yosys_binary']);runtime=Path(m['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');(D/'protocol.json').write_text(json.dumps({'scope':'Abstract binary old/new whole-word read at collision, width256 matching2remaining source message RAMs. Compare globally shared read choice and independent per-lane choices. Demonstrates coherence obligation, not actual mapped scheduler behavior, reset-reachable word values, source4state equivalence or physical RAM read mode.','bindings':{str(p):sha(p) for p in [Path(__file__),binary,runtime]}},indent=2)+'\n');v=D/'coherence.v';v.write_text('''module proof(input[255:0]old_word,new_word,choices,input global_choice,output shared_ok,lane_member,lane_aux_member,output[255:0]shared_word,mixed_word);
assign shared_word=global_choice?new_word:old_word;
assign mixed_word=(choices & new_word)|(~choices & old_word);
assign shared_ok=(shared_word==old_word)||(shared_word==new_word);
assign lane_member=(mixed_word==old_word)||(mixed_word==new_word);
assign lane_aux_member=((&mixed_word)==(&old_word))||((&mixed_word)==(&new_word));
endmodule
''');tests=[('shared_choice','-prove shared_ok 1',True),('independent_lane_negative','-prove lane_member 1',False),('auxiliary_conjunction_negative','-prove lane_aux_member 1',False)];rows=[]
 for name,proof,positive in tests:
  f=D/name;f.mkdir();ys=f/'commands.ys';ys.write_text(f'read_verilog {v}\nhierarchy -top proof\nproc\nopt\ncheck -assert\nsat {proof} -show old_word,new_word,choices,mixed_word -dump_json {f/"witness.json"} -verify\n')
  with (f/'yosys.log').open('w') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=log,stderr=subprocess.STDOUT)
  text=(f/'yosys.log').read_text();rows.append({'name':name,'exit_code':code,'proof_passed':'no model found: SUCCESS' in text,'proof_failed':'proof did fail' in text});print(rows[-1],flush=True)
 # Independent explicit witness; both valid complete old/new words reduce to0, mixed word reduces1.
 mask=(1<<256)-1;old=mask^1;new=mask^2;choices=1;mixed=(choices&new)|((~choices)&old&mask);assert old!=mask and new!=mask and mixed==mask
 (D/'explicit_witness.json').write_text(json.dumps({'width':256,'old_hex':format(old,'064x'),'new_hex':format(new,'064x'),'lane_choices_hex':format(choices,'064x'),'mixed_hex':format(mixed,'064x'),'old_reduce_AND':0,'new_reduce_AND':0,'mixed_reduce_AND':1,'scope':'Abstract independent lane choices only; not a reset-reachable source or actual mapper witness.'},indent=2)+'\n');(D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
