"""Isolated linker-wrap VPR pressure consumer; shared object/archive inputs read only."""
import json,shlex,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path('../tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07').resolve()
build=root/'build_tileplace_vpr/vpr';out=Path('build/native_packing_fault_stages_2026-10-06').resolve();out.mkdir();(out/'source').mkdir()
source=Path('tools/native_packing_fault_stages/hook.cpp').resolve();shutil.copyfile(source,out/'source/hook.cpp');shutil.copyfile(__file__,out/'source/build.py')
flags={}
for line in (build/'CMakeFiles/vpr.dir/flags.make').read_text().splitlines():
 if ' = ' in line:
  k,v=line.split(' = ',1);flags[k]=shlex.split(v)
obj=out/'hook.o';exe=out/'routecast_packing_rollback_vpr'
compile=['/usr/bin/c++',*flags['CXX_DEFINES'],*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],'-c',str(source),'-o',str(obj)]
link=shlex.split((build/'CMakeFiles/vpr.dir/link.txt').read_text())
link=[str(exe) if x=='vpr' else str((build/x).resolve()) if x.endswith(('.a','.o')) else x for x in link]
link[1:1]=[str(obj),'-Wl,--wrap=_Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb']
shared_archive=build/'libvpr.a';shared_archive_sha=sha(shared_archive)
cpp=(root/'vpr/src/pack/post_routing_pb_pin_fixup.cpp').read_text()
helper="""#include <cstdlib>
#include <stdexcept>
#include <new>
static void routecast_sync_fault(int stage){
 if(const char* value=std::getenv("ROUTECAST_SYNC_FAULT_STAGE"))if(std::atoi(value)==stage){
  VTR_LOG("ROUTECAST sync fault reached stage=%d\\n",stage);
  if(const char* kind=std::getenv("ROUTECAST_SYNC_FAULT_KIND"))if(std::string(kind)=="bad_alloc")throw std::bad_alloc();
  throw std::runtime_error("injected packing stage error");
 }
}
"""
# Insert helper after includes and before first function; logger declarations visible.
pos=cpp.index('static void update_cluster_pin_with_post_routing_results')
cpp=cpp[:pos]+helper+cpp[pos:]
cpp=cpp.replace('    clustering_ctx.pre_routing_net_pin_mapping.clear();','    clustering_ctx.pre_routing_net_pin_mapping.clear();\n    routecast_sync_fault(1);',1)
needle='                                                                    verbose);'
# Stage2 after first actual block-routing update in main loop, not helper calls.
start=cpp.index('void sync_netlists_to_routing(')
part=cpp[start:];target=part.index(needle);part=part[:target]+part[target:].replace(needle,needle+'\n            routecast_sync_fault(2);',1)
part=part.replace('    /* Print a short summary */','    routecast_sync_fault(3);\n    /* Print a short summary */',1);cpp=cpp[:start]+part
file=out/'source/post_routing_pb_pin_fixup.cpp';file.write_text(cpp);extra=out/'sync.o';cmd=compile[:-4]+['-c',str(file),'-o',str(extra)]
with (out/'sync_compile.log').open('w') as f:code=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=120).returncode
if code:raise SystemExit('sync compile failed')
private_archive=out/'libvpr.a';shutil.copyfile(shared_archive,private_archive);subprocess.run(['ar','d',str(private_archive),'post_routing_pb_pin_fixup.cpp.o'],check=True)
link=[str(private_archive) if p==str(shared_archive) else p for p in link];link[1:1]=[str(extra)]
inputs={x:sha(x) for x in link if x.endswith(('.a','.o')) and x!=str(obj)}
protocol={'compile':compile,'link':link,'inputs_sha256':inputs,'source_sha256':sha(source),'build_source_sha256':sha(__file__),'scope':'private wrapper plus original unchanged main/object/archives; absent pressure environment forwards original initialization; experimental cost warm start only'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
for stage,command in [('compile',compile),('link',link)]:
 with (out/(stage+'.log')).open('w') as log:
  r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 if r.returncode:
  print(stage+' failed',flush=True);raise SystemExit(r.returncode)
assert sha(shared_archive)==shared_archive_sha
assert all(sha(p)==h for p,h in inputs.items()) and sha(source)==protocol['source_sha256']
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'binary_sha256':sha(exe),'wall_s':time.monotonic()-start,'shared_inputs_unchanged':True,'zero_feedback_parity_verified':False},indent=2)+'\n');print(exe,flush=True)
