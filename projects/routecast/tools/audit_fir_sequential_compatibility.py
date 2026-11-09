"""Audit all frozen FIR cases without removing asynchronous reset semantics."""
import collections,json,shutil,subprocess
from pathlib import Path
from pre_route_endpoints import sha
from reconstruct_vexriscv_sequential_netlist import logical_lines

base=Path('experiments');parent=base/'fir_family_frontend_2026-10-06';protocol=json.loads((parent/'protocol.json').read_text());candidates=base/'prospective_family_candidates_2026-10-06';tool=json.loads((candidates/'frontend_availability.json').read_text());yosys=Path(tool['yosys_path']);assert sha(yosys)==protocol['yosys_sha256'];out=base/'fir_family_sequential_compatibility_v2_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py');results=[]
architecture=Path('../tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml');architecture_text=architecture.read_text();arch_hash=sha(architecture)
for record in protocol['inputs']:
 path=Path(record['archived_path']);assert sha(path)==record['sha256'];work=out/path.stem;work.mkdir();shutil.copyfile(path,work/'design.v');command=[str(yosys),'-p','read_verilog design.v; synth -top fir -flatten; dffunmap; check -assert; write_blif flat.blif']
 with (work/'synth.log').open('w') as log:code=subprocess.run(command,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
 if code!=0:
  result={'design':path.stem,'exit_code':code,'vpr_ready':False,'source_sha256':sha(path),'synth_log_sha256':sha(work/'synth.log'),'reason':'Yosys source/frontend rejected; inspect archived log'};results.append(result);print(json.dumps(result),flush=True);continue
 lines=list(logical_lines(work/'flat.blif'));cells=collections.Counter(line.split()[1] for line in lines if line.startswith('.subckt '));unsupported=sorted(c for c in cells if c not in architecture_text)
 result={'design':path.stem,'subckt_counts':dict(cells),'architecture_missing_models':unsupported,'vpr_ready':False,'source_sha256':sha(path),'flat_blif_sha256':sha(work/'flat.blif'),'synth_log_sha256':sha(work/'synth.log'),'exit_code':code};results.append(result);print(json.dumps(result),flush=True)
assert sha(yosys)==protocol['yosys_sha256'] and sha(architecture)==arch_hash
(out/'receipt.json').write_text(json.dumps({'frontend_protocol_sha256':sha(parent/'protocol.json'),'source_sha256':sha(__file__),'architecture_sha256':arch_hash,'results':results,'scope':'FIR frozen 2x2 candidate family has unsupported asynchronous state cells; no state rewrite, ABC CEC claim, native run or unseen-family claim'},indent=2)+'\n')
