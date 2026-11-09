"""Bounded native pack-only diagnosis using experimental reset architecture."""
import json,os,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_native_ram_pack_v2_2026-10-09';D.mkdir(exist_ok=False)
proof=E/'full_ram_native_slices_v1_2026-10-09/verification.json';doc=json.loads(proof.read_text());assert all(sha(p)==h for p,h in doc['bindings'].items())
source=E/'full_ram_native_slices_v1_2026-10-09/design.blif';arch=E/'async_reset_arch_candidate_v2_2026-10-08/architecture.xml';vpr=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_vpr/vpr/vpr';shutil.copyfile(source,D/'design.blif')
bindings={str(p):sha(p) for p in (Path(__file__).resolve(),proof,source,arch,vpr,D/'design.blif')};cmd=[str(vpr),str(arch),'design.blif','--pack','--route_chan_width','128','--num_workers','1','--seed','1'];plan=dict(bindings=bindings,command=cmd,timeout_s=600,scope='Complete Full native RAM candidate pack compatibility trial after independent reconstruction/readback proof; fixed600s budget frozen before launch. 300 one-bit RAM atoms representing 15 wide candidates and initialized controls retained in BLIF; pack-only diagnosis, native treatment of initialization must be audited; experimental async reset architecture with placeholder reset timing. No placement/routing labels, no heldout or physical performance claim.')
(D/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');tick=time.perf_counter()
with (D/'pack.log').open('x') as log:
 try:code=subprocess.run(cmd,cwd=D,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
assert all(sha(p)==h for p,h in bindings.items())
files={str(p):sha(p) for p in D.iterdir() if p.is_file()}
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,files=files,exit_code=code,seconds=time.perf_counter()-tick,pack_net_exists=(D/'design.net').exists(),admitted_for_prediction=False,scope=plan['scope']),indent=2)+'\n');print(dict(exit_code=code,pack_net_exists=(D/'design.net').exists(),seconds=time.perf_counter()-tick),flush=True)
