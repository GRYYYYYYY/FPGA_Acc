"""Isolated linker-wrap VPR pressure consumer; shared object/archive inputs read only."""
import json,shlex,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path('../tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07').resolve()
build=root/'build_tileplace_vpr/vpr';out=Path('build/native_net_identity_early_capture_2026-10-07').resolve();out.mkdir();(out/'source').mkdir()
source=Path('tools/native_net_identity_capture/hook_early_v1.cpp').resolve();shutil.copyfile(source,out/'source/hook.cpp');shutil.copyfile(__file__,out/'source/build.py')
flags={}
for line in (build/'CMakeFiles/vpr.dir/flags.make').read_text().splitlines():
 if ' = ' in line:
  k,v=line.split(' = ',1);flags[k]=shlex.split(v)
obj=out/'hook.o';exe=out/'routecast_net_identity_vpr'
compile=['/usr/bin/c++',*flags['CXX_DEFINES'],*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],'-c',str(source),'-o',str(obj)]
link=shlex.split((build/'CMakeFiles/vpr.dir/link.txt').read_text())
link=[str(exe) if x=='vpr' else str((build/x).resolve()) if x.endswith(('.a','.o')) else x for x in link]
link[1:1]=[str(obj),'-Wl,--wrap=_Z15create_rr_graph12e_graph_typeRKSt6vectorI20t_physical_tile_typeSaIS1_EERK10DeviceGridRK12t_chan_widthP18t_det_routing_archRKS0_I13t_segment_infSaISE_EERK13t_router_optsRKS0_I12t_direct_infSaISM_EEPib']
inputs={x:sha(x) for x in link if x.endswith(('.a','.o')) and x!=str(obj)}
protocol={'compile':compile,'link':link,'inputs_sha256':inputs,'source_sha256':sha(source),'build_source_sha256':sha(__file__),'scope':'private wrapper plus original unchanged main/object/archives; absent pressure environment forwards original initialization; experimental cost warm start only'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
for stage,command in [('compile',compile),('link',link)]:
 with (out/(stage+'.log')).open('w') as log:
  r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 if r.returncode:
  print(stage+' failed',flush=True);raise SystemExit(r.returncode)
assert all(sha(p)==h for p,h in inputs.items()) and sha(source)==protocol['source_sha256']
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'binary_sha256':sha(exe),'wall_s':time.monotonic()-start,'shared_inputs_unchanged':True,'zero_feedback_parity_verified':False},indent=2)+'\n');print(exe,flush=True)
