"""Same-target reference/candidate selection with canonical view restoration."""
import json
import re
import subprocess
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/native_candidate_move_accept_scoped_2026-10-06'
source=ROOT/'build/loaded_native_quality_gate_2026-10-06/source/route.cpp'
out=ROOT/'build/loaded_native_quality_gate_v2_2026-10-06';out.mkdir();src=out/'source';src.mkdir()
p=json.loads((ROOT/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text())
shared={f:sha(f) for f in p['inputs_sha256']}
s=source.read_text()
needle='                    print_route(net_list,reference_file,is_flat);'
assert s.count(needle)==1
s=s.replace(needle,'                    std::fprintf(reference_file,"Placement_File: candidate.place Placement_ID: %s\\nArray size: %zu x %zu logic blocks.\\n\\nRouting:\\n",g_vpr_ctx.placement().placement_id.c_str(),device_ctx.grid.width(),device_ctx.grid.height());\n'+needle,1)
(src/'route.cpp').write_text(s)
compile_cmd=[*p['compile'][:-4],'-c',str(src/'route.cpp'),'-o',str(out/'route.o')]
link=[str(base/'libvpr.a') if x.endswith('/libvpr.a') else str(out/'gate_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']]
link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')]
wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(ROOT/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1]
link[1:1]=[str(base/'read_route.o'),str(base/'old_traceback.o'),str(out/'route.o'),str(base/'sync_once.o'),wrap]
(out/'protocol.json').write_text(json.dumps(dict(compile=compile_cmd,link=link,shared_inputs_sha256=shared,parent_source_sha256=sha(source),source_sha256=sha(src/'route.cpp')),indent=2)+'\n')
for label,cmd in [('compile',compile_cmd),('link',link)]:
    with (out/(label+'.log')).open('w') as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
    if code:raise SystemExit(label+' failed '+str(code))
assert all(sha(f)==h for f,h in shared.items())
(out/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(out/'gate_vpr'),protocol_sha256=sha(out/'protocol.json'),scope='One-step same-target CPD gate; reference winner reimport resets search cost metadata, not exact full router checkpoint restoration. Runtime/quality/evidence pending.'),indent=2)+'\n')
print('built loaded same-target quality gate')
