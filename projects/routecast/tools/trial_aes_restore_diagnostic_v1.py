import os,json,subprocess,shutil,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pre_route_endpoints import sha
r=Path.cwd();out=r/'experiments/aes_restore_diagnostic_v1_2026-10-08';out.mkdir();source=r/'experiments/aes_mapped_full_workflow_v1_2026-10-08/aes_cipher';vpr=r/'build/aes_restore_diagnostic_v1_2026-10-08/sequence_vpr';arch=r.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml';graph=r/'experiments/aes_rr_graph_only_v1_2026-10-08/aes_cipher/rr_graph.xml'
for f in ['design.blif','design.net','design.place','seed.route']:shutil.copyfile(source/f,out/f)
cmd=[str(vpr),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
bindings={str(f):sha(f) for f in [Path(__file__),vpr,arch,graph,*[out/f for f in ['design.blif','design.net','design.place','seed.route']]]};(out/'protocol.json').write_text(json.dumps({'command':cmd,'bindings':bindings,'scope':'Diagnostic logging only; identical frozen cipher seed and inputs. Not an accepted route.'},indent=2)+'\n');start=time.perf_counter()
with (out/'native.log').open('w') as f:code=subprocess.run(cmd,cwd=out,env={**{k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},'ROUTECAST_NATIVE_SEED':str(out/'seed.route')},stdout=f,stderr=subprocess.STDOUT,timeout=120).returncode
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'exit_code':code,'seconds':time.perf_counter()-start,'bindings':bindings,'log_sha256':sha(out/'native.log')},indent=2)+'\n');print(code)
