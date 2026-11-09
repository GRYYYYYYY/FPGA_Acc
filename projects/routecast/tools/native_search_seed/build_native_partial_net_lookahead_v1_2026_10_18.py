"""Isolated file-partial-NET seed support: preserve missing-sink lookahead delay."""
import json,sys,subprocess,re,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
B=R/'build/native_candidate_retained_search_2026-10-06';bp=B/'receipt.json';b=json.loads(bp.read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['source_sha256'].items()) and all(sha(p)==h for p,h in b['shared_inputs_sha256'].items());base=R/'build/native_candidate_move_accept_scoped_2026-10-06';D=R/'build/native_partial_net_lookahead_v1_2026-10-18';D.mkdir();src=D/'source';src.mkdir();old=B/'source/route.cpp';text=old.read_text();needle='                    if (!sink) throw std::runtime_error("incomplete seed delay map");';assert text.count(needle)==1 and text.count('throw std::runtime_error("incomplete seed delay map")')==2
replacement='                    if (!sink) continue; // File partial-NET seed: retain initialized lookahead for an unrouted sink.'
changed=text.replace(needle,replacement);assert changed.count('throw std::runtime_error("incomplete seed delay map")')==1 and 'router_opts.initial_timing != e_router_initial_timing::LOOKAHEAD' in changed
with (src/'route.cpp').open('x') as f:f.write(changed)
shutil.copyfile(__file__,src/'build.py');protocol=R/'build/native_seed_import_v2_2026-10-06/protocol.json';p=json.loads(protocol.read_text());obj=D/'route.o';compile=[*p['compile'][:-4],'-c',str(src/'route.cpp'),'-o',str(obj)]
link=[str(base/'libvpr.a') if x.endswith('/libvpr.a') else str(D/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(R/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1];link[1:1]=[str(base/'read_route.o'),str(base/'old_traceback.o'),str(obj),str(base/'sync_once.o'),wrap]
inputs=[bp,old,protocol,base/'libvpr.a',base/'read_route.o',base/'old_traceback.o',base/'sync_once.o'];bindings={**closure([Path(__file__)]),**b['source_sha256'],**b['shared_inputs_sha256'],**{str(p):sha(p) for p in inputs}}
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,compile=compile,link=link,old_binary_sha256=b['binary_sha256'],edit='Only LOOKAHEAD seeded existing-tree missing sink: keep already initialized lookahead estimate instead of throwing. Non-lookahead and inprocess retained completeness guards unchanged.',scope='New isolated build; no partial import, runtime correctness or no-seed/full-NET equivalence claimed until actual validation.'),f,indent=2)
print('PARTIAL NET BUILD COMPILE START',flush=True)
with (D/'compile.log').open('x') as log:subprocess.run(compile,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=None)
print('PARTIAL NET BUILD LINK START',flush=True)
with (D/'link.log').open('x') as log:subprocess.run(link,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=None)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings={**bindings,str(src/'route.cpp'):sha(src/'route.cpp'),str(src/'build.py'):sha(src/'build.py'),str(D/'protocol.json'):sha(D/'protocol.json')},binary_sha256=sha(D/'sequence_vpr'),only_lookahead_missing_sink_guard_changed=True,runtime_equivalence_pending=True,partial_seed_completion_pending=True),f,indent=2)
print('PARTIAL NET ISOLATED BUILD PASS',flush=True)
