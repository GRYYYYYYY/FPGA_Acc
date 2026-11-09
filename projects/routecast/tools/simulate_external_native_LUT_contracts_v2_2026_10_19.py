"""Native LUT_K four-state simulation: default-X and explicit ground contracts."""
import json,subprocess,time,resource,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/prospective_external_family_LUT_fourstate_v2_2026-10-19';out.mkdir(exist_ok=False);native=R/'experiments/prospective_external_family_native_packed_LUTs_v1_2026-10-19';proof=native/'verification.json';pv=read(proof);assert all(sha(p)==h for p,h in pv['bindings'].items());refpath=R/'experiments/prospective_external_family_LUT_reference_v1_2026-10-19/derived_physical_LUTs.jsonl';refs={r['atom']:r for r in map(json.loads,refpath.open())};loaded={}
 for line in (native/'loaded_LUTs.tsv').open():
  name,w,signals,mask=line.rstrip('\n').split('\t');loaded[name]=(int(w),signals.split(','),mask)
 assert set(loaded)==set(refs) and len(loaded)==6483
 runtime=R/'experiments/prospective_external_family_sim_runtime_v1_2026-10-18/root/usr';iv=runtime/'bin/iverilog';vvp=runtime/'bin/vvp';lib=runtime/'lib/x86_64-linux-gnu/ivl';primitives=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/primitives.v';tb=out/'contracts_tb.v';expected=0;expected_x=0
 source=primitives.read_text();module=re.search(r'(?m)^module LUT_K\b.*?^endmodule',source,re.S|re.M).group(0);blocks=re.findall(r'\bspecify\b.*?\bendspecify\b',module,re.S);assert len(blocks)==1 and '(in *> out)' in blocks[0];functional_text=module.replace(blocks[0],'');assert 'assign out = LUT_MASK[in];' in functional_text;functional=out/'LUT_K_functional_only.v';functional.write_text(functional_text+'\n')
 with tb.open('x') as f:
  f.write('module contracts_tb; reg [5:0] stimulus; integer i; integer gchecks=0; integer xchecks=0; integer unknowns=0;\n')
  for k,(name,(w,signals,mask)) in enumerate(loaded.items()):
   r=refs[name];rot=r['physical_to_logical'];logical=r['logical_truth'];n=len(r['logical_inputs']);expected+=1<<n
   if 'open' in rot:expected_x+=1<<n
   xins=','.join("1'bx" if j=='open' else f'stimulus[{j}]' for j in reversed(rot));gins=','.join("1'b0" if j=='open' else f'stimulus[{j}]' for j in reversed(rot));f.write(f"wire g{k}, x{k}; localparam [{len(logical)-1}:0] E{k}={len(logical)}'b{logical[::-1]};\nLUT_K #(.K({w}),.LUT_MASK({len(mask)}'b{mask[::-1]})) G{k}(.in({{{gins}}}),.out(g{k}));\nLUT_K #(.K({w}),.LUT_MASK({len(mask)}'b{mask[::-1]})) X{k}(.in({{{xins}}}),.out(x{k}));\n")
  f.write('initial begin for(i=0;i<64;i=i+1) begin stimulus=i; #1;\n')
  for k,(name,(w,signals,mask)) in enumerate(loaded.items()):
   r=refs[name];n=len(r['logical_inputs']);hasopen='open' in r['physical_to_logical'];expect="1'bx" if hasopen else f'E{k}[i]';f.write(f'if(i<{1<<n}) begin gchecks=gchecks+1; xchecks=xchecks+1; if(g{k} !== E{k}[i]) $fatal(1,"ground mismatch atom{k} input%0d",i); if(x{k} !== {expect}) $fatal(1,"X-contract mismatch atom{k} input%0d",i);')
   if hasopen:f.write(f'if(x{k} === 1\'bx) unknowns=unknowns+1;')
   f.write('end\n')
  f.write(f'end if(gchecks!={expected} || xchecks!={expected} || unknowns!={expected_x}) $fatal(1,"coverage"); $display("NATIVE_LUT_CONTRACTS_PASS gchecks=%0d xchecks=%0d unknowns=%0d",gchecks,xchecks,unknowns); $finish; end endmodule\n')
 image=out/'contracts.vvp';compilecmd=[str(iv),'-B',str(lib),'-g2012','-s','contracts_tb','-o',str(image),str(functional),str(tb)];simcmd=[str(vvp),'-M',str(lib),str(image)];paths=[proof,refpath,native/'loaded_LUTs.tsv',primitives,functional,tb,iv,vvp,Path(__file__).resolve(),*[p for p in lib.iterdir() if p.is_file()]];bindings={str(p):sha(p) for p in paths};protocol=dict(compile_command=compilecmd,simulation_command=simcmd,bindings=bindings,LUT_atoms=6483,expected_each_contract_assignments=expected,expected_default_X_observations=expected_x,scope='Two explicitly separate LUT-level contracts under exact native LUT_K functional body; only specify timing block removed in isolated derived source for Icarus compatibility. No timing validation. No silent change to writer default. Native masks loaded from packed state; all logical assignments. Does not simulate full packed circuit, establish reachability/primary-output propagation, original HDL equivalence or family admission.');(out/'protocol.json').write_text(json.dumps(protocol,indent=2));tick=time.perf_counter()
 def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 with (out/'compile.log').open('x') as log:c=subprocess.run(compilecmd,cwd=out,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
 if c.returncode:raise RuntimeError('Icarus compile failed; log retained')
 with (out/'simulation.log').open('x') as log:s=subprocess.run(simcmd,cwd=out,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
 text=(out/'simulation.log').read_text();passed=s.returncode==0 and f'NATIVE_LUT_CONTRACTS_PASS gchecks={expected} xchecks={expected} unknowns={expected_x}' in text
 for p,h in bindings.items():assert sha(p)==h
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='BOTH_NATIVE_LUT_GROUND_AND_DEFAULT_X_CONTRACTS_EXHAUSTIVELY_SIMULATED' if passed else 'NATIVE_LUT_CONTRACT_SIMULATION_FAILED',passed=passed,compile_exit_code=c.returncode,simulation_exit_code=s.returncode,each_contract_assignments=expected,default_X_observations=expected_x,component_seconds=time.perf_counter()-tick,bindings={str(p):sha(p) for p in [out/'protocol.json',out/'compile.log',out/'simulation.log',image]},scope=protocol['scope']),f,indent=2)
 print(text.strip());assert passed
if __name__=='__main__':main()
