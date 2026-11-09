"""Defined write-initialized cross-port collision trace on pinned standard IR."""
import json,hashlib,subprocess,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'standard_ram_collision_sat_v1_2026-10-21';SRC=E/'ram_mapping_semantics_v1_2026-10-20/standard_nomem2reg_disabled_port/constant_zero_we2/proc.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);m=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(m['yosys_binary']);runtime=Path(m['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');protocol={'scope':'Pinned tiny standard functional RAM IR, ADDR1/DATA2, second writer tied0. Three RTLIL states initial+two updates; state1 write address0=1, state2 write same address0=2 with port2 reading0. State3 out1 must2; test out2 old1 versus new2. No initial state values assumed. Not whole source/hardware equivalence.','bindings':{str(p):sha(p) for p in [Path(__file__),SRC,binary,runtime]}};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for label,expected in [('old_data',1),('new_data',2)]:
  f=D/label;f.mkdir();ys=f/'commands.ys';ys.write_text(f'read_json {SRC}\nhierarchy -top probe\nmemory -nomap\nmemory_map\nopt_clean\ncheck -assert\nsat -seq 3 -enable_undef -set-def-inputs -set we2 0 -set we1 1 -set addr1 0 -set addr2 0 -set data1 2 -set data2 0 -set-at 1 data1 1 -prove out1 2 -prove out2 {expected} -prove-skip 2 -show out1,out2 -verify\n');
  with (f/'yosys.log').open('w') as out:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=out,stderr=subprocess.STDOUT)
  log=(f/'yosys.log').read_text();rows.append({'hypothesis':label,'expected_out2':expected,'exit_code':code,'sat_proof_success':'SAT proof finished - no model found: SUCCESS!' in log,'proof_failed':'proof did fail' in log});print(rows[-1],flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
