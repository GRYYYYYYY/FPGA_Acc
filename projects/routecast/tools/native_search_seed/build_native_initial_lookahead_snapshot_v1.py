"""Only log original criticality return values; all router objects remain frozen."""
import json,subprocess,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
R=Path.cwd();B=R/'build/native_live_seed_manifest_scope_v1_2026-10-10';D=R/'build/native_initial_lookahead_snapshot_v1_2026-10-17';D.mkdir();b=json.loads((B/'receipt.json').read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['source_sha256'].items())
inputs=R/'build/native_candidate_move_accept_scoped_2026-10-06';nm=subprocess.check_output(['nm',str(inputs/'libvpr.a')],text=True);symbols=[line.split()[-1] for line in nm.splitlines() if ' T _Z23get_net_pin_criticality' in line];assert len(symbols)==1;symbol=symbols[0]
template=R/'tools/native_search_seed/initial_lookahead_observer_v1.cpp'
source=template.read_text().replace('REAL','__real_'+symbol).replace('WRAP','__wrap_'+symbol)
delay_symbols=[line.split()[-1] for line in nm.splitlines() if ' T ' in line and 'init_net_delay_from_lookahead' in line];assert len(delay_symbols)==1;delay_symbol=delay_symbols[0]
source=source.replace('DELAY_ORIGINAL','__real_'+delay_symbol).replace('DELAY_WRAPPER','__wrap_'+delay_symbol)
(D/'observer.cpp').write_text(source)
p=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());compile=[*p['compile'][:-4],'-c',str(D/'observer.cpp'),'-o',str(D/'observer.o')]
with (D/'compile.log').open('w') as log:subprocess.run(compile,stdout=log,stderr=subprocess.STDOUT,check=True)
link=[str(inputs/'libvpr.a') if x.endswith('/libvpr.a') else str(D/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')]
wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(R/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1]
link[1:1]=[str(inputs/'read_route.o'),str(inputs/'old_traceback.o'),str(B/'route.o'),str(inputs/'sync_once.o'),str(D/'observer.o'),wrap,'-Wl,--wrap='+symbol,'-Wl,--wrap='+delay_symbol]
with (D/'link.log').open('w') as log:subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True)
vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src'
files=[template,vendor/'route/route_utils.h',vendor/'route/route_net.cpp',vendor/'timing/timing_info.h',vendor/'timing/timing_util.h',vendor/'timing/timing_util.cpp',vendor/'base/clustered_netlist_utils.h',Path(__file__),B/'receipt.json',B/'route.o',inputs/'libvpr.a',D/'observer.cpp',D/'observer.o']
bindings={**b['bindings'],**b['source_sha256'],**{str(p.resolve()):sha(p) for p in files}}
assert all(sha(p)==h for p,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,binary_sha256=sha(D/'sequence_vpr'),symbol=symbol,delay_symbol=delay_symbol,compile=compile,link=link,scope='At first criticality invocation, preserve original transformed criticality rows; enumerate every clustered sink and all connected atoms with exact float bits, native/manual min-slack/max-criticality equality, ignored/global/clock flags; exit before first getter returns. Worst-path slack is not a connection additive budget. No completed route, predictor or performance claim.'),indent=2)+'\n');print('INITIAL TIMING OBSERVER BUILD PASS')
