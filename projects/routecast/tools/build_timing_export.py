"""Read-only existing VPR archives link to isolated custom main."""
import json,shlex,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path('../tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07').resolve();build=root/'build_tileplace_vpr/vpr';out=Path('build/timing_export_v7_2026-10-04').resolve()
if out.exists():raise ValueError('fresh build required')
out.mkdir();(out/'source').mkdir();
import shutil
for f in Path('tools/native_timing').glob('*'):shutil.copyfile(f,out/'source'/f.name)
flags={}
for line in (build/'CMakeFiles/vpr.dir/flags.make').read_text().splitlines():
    if ' = ' in line:k,v=line.split(' = ',1);flags[k]=shlex.split(v)
source=Path('tools/native_timing/main.cpp').resolve();obj=out/'main.o';exe=out/'routecast_timing_export';compile=['/usr/bin/c++',*flags['CXX_DEFINES'],*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],'-I'+str(source.parent),'-c',str(source),'-o',str(obj)]
link=shlex.split((build/'CMakeFiles/vpr.dir/link.txt').read_text());link=[str(obj) if x=='CMakeFiles/vpr.dir/src/main.cpp.o' else str(exe) if x=='vpr' else str((build/x).resolve()) if x.endswith('.a') else x for x in link]
libs={x:sha(x) for x in link if x.endswith('.a')};p={'compile':compile,'link':link,'shared_libraries':libs,'source_sha256':{str(f):sha(f) for f in source.parent.glob('*')},'scope':'compile one private translation unit, existing shared VPR build read-only'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic()
for stage,cmd in [('compile',compile),('link',link)]:
    with (out/f'{stage}.log').open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    if r.returncode:print(stage+' failed');raise SystemExit(r.returncode)
assert all(sha(f)==v for f,v in libs.items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'executable_sha256':sha(exe),'elapsed_s':time.monotonic()-start,'shared_archives_unchanged':True},indent=2)+'\n');print(exe)
