"""Private read-only post-STA capture, original source reversibly preserved."""
import json,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 base=R/'build/native_iteration_state_observer_v1_2026-10-10';out=R/'build/dense_post_STA_source_v1_2026-10-18';out.mkdir(exist_ok=False);bp=base/'receipt.json';b=json.loads(bp.read_text());assert all(sha(k)==h for k,h in b['bindings'].items());sp=R/'experiments/mmc_dense_post_STA_source_protocol_v1_2026-10-18/protocol.json';spec=json.loads(sp.read_text());assert all(sha(k)==h for k,h in spec['bindings'].items());inc=R/'tools/native_search_seed/dense_post_STA_capture_v1.inc';hook=inc.read_text();original=(base/'route.cpp').read_text();needle='        pin_timing_invalidator->reset();\n';include='#include "route_net.h"\n';assert original.count(needle)==1 and include not in original;patched=include+original.replace(needle,needle+'\n'+hook);assert patched.replace(include,'',1).replace('\n'+hook,'',1)==original;(out/'route.cpp').write_text(patched);before=original.index('        timing_info->update();');site=patched.index('// ROUTECAST_DENSE_POST_STA_CAPTURE_BEGIN');assert patched.index('        timing_info->update();')<patched.index(needle)<site
 compile=[*b['compile'][:-4],'-I'+str(R/'build/native_live_seed_manifest_scope_v1_2026-10-10/source'),'-c',str(out/'route.cpp'),'-o',str(out/'route.o')];link=[str(out/'route.o') if x==str(base/'route.o') else str(out/'sequence_vpr') if x==str(base/'sequence_vpr') else x for x in b['link']];bindings={**b['bindings'],**closure([Path(__file__)]),str(bp):sha(bp),str(sp):sha(sp),str(inc):sha(inc),str(out/'route.cpp'):sha(out/'route.cpp')};(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,compile=compile,link=link,original_source_recovered_exactly=True,phase='after timing_info update and pin timing invalidator reset; feasible iterations only'),indent=2));tick=time.perf_counter()
 with (out/'compile.log').open('x') as log:subprocess.run(compile,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 compile_seconds=time.perf_counter()-tick;tick=time.perf_counter()
 with (out/'link.log').open('x') as log:subprocess.run(link,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 link_seconds=time.perf_counter()-tick;assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,binary_sha256=sha(out/'sequence_vpr'),compile_seconds=compile_seconds,link_seconds=link_seconds,original_source_recovered_exactly=True,scope='Private post-STA data export only. Runtime route/work equality, dense physical identity and phase admission pending.'),indent=2));print('DENSE_POST_STA_BUILD_COMPLETE',compile_seconds,link_seconds,flush=True)
if __name__=='__main__':main()
