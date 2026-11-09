"""Compare archived old/new cold native inputs; no new routing or causal claim."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_cold_route_turnover_v1_2026-10-18';bindings=closure([Path(__file__)]);rows=[]
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 proof=load(root/'independent_verification_v1.json');assert proof['status']=='all3_independent_old_and_cold_native_token_union_and_exact_error_decompositions_pass'
 oldroot=E/'ultraembedded_mmc_limited_expat_workflow_v16_2026-10-10';op=load(oldroot/'protocol.json');outer=load(oldroot/'receipt.json');old=oldroot/'cold/native/mmc';rp=old/'receipt.json';receipt=load(rp);assert outer['files'][str(rp)]==sha(rp) and outer['files'][str(old/'output.route')]==sha(old/'output.route');base=receipt['command']
 for case in ['case_01','case_02','case_03']:
  newroot=E/f'mmc_multiplacement_cold_labels_v1_2026-10-18/{case}';p=load(newroot/'protocol.json');v=load(newroot/'verification.json');assert v['all_native_physical_and_canonical_pass'];cmd=p['commands']['cold'];normalized=[];inputs={}
  for label,command,cwd,cert in [('old',base,old,receipt['files']),('target',cmd,newroot/'cold',v['bindings'])]:
   vals=list(command);binary=Path(vals[0]);arch=Path(vals[1]);rr=Path(vals[vals.index('--read_rr_graph')+1]);expected=op['bindings'] if label=='old' else p['bindings']
   for path in [binary,arch]:assert sha(path)==expected[str(path)];bindings[str(path)]=sha(path)
   assert sha(rr)==(receipt['bindings'][str(rr)] if label=='old' else p['bindings'][str(rr)]);bindings[str(rr)]=sha(rr);vals[0]=sha(binary);vals[1]=sha(arch);vals[vals.index('--read_rr_graph')+1]=sha(rr);digests={}
   for filename in ['design.blif','design.net','design.place']:
    path=cwd/filename;h=sha(path);assert cert[str(path)]==h;bindings[str(path)]=h;digests[filename]=h
   vals[2]=digests['design.blif'];normalized.append(vals);inputs[label]=digests
  assert normalized[0]==normalized[1];assert inputs['old']['design.blif']==inputs['target']['design.blif'] and inputs['old']['design.net']==inputs['target']['design.net'] and inputs['old']['design.place']!=inputs['target']['design.place'];rows.append(dict(case=case,normalized_commands_equal=True,binary_arch_RR_BLIF_packed_net_and_flags_equal=True,placement_bytes_differ=True,input_sha256=inputs,seed=cmd[cmd.index('--seed')+1],num_workers=cmd[cmd.index('--num_workers')+1]))
 assert all(sha(k)==h for k,h in bindings.items());(root/'native_input_equivalence_v1.json').open('x').write(json.dumps(dict(status='all3_archived_common_native_inputs_and_recorded_commands_equal_except_placement_content',bindings=bindings,cases=rows,limits='Same archived binary, architecture, RR bytes, BLIF, packed NET, all command flags, seed and worker count. Placement content differs as intended. This does not certify identical external runtime environment or separate deterministic placement effects from any unmeasured repeat variation; no new same-placement rerun was executed. It excludes a recorded solver-policy or graph-content mismatch as explanation of the turnover.'),indent=2));print('all3 recorded native inputs match except placement',flush=True)
if __name__=='__main__':main()
