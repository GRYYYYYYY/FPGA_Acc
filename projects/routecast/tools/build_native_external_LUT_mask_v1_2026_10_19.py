"""Link isolated harness against existing native VPR libraries, read-only vendor."""
import json,shlex,subprocess
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def main():
 vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';build=vendor/'build_tileplace_vpr';out=R/'experiments/prospective_external_family_native_LUT_masks_v1_2026-10-19';out.mkdir(exist_ok=False);flags=build/'vpr/CMakeFiles/libvpr.dir/flags.make';lines=dict(line.split(' = ',1) for line in flags.read_text().splitlines() if ' = ' in line);linkfile=build/'vpr/CMakeFiles/vpr.dir/link.txt';old=shlex.split(linkfile.read_text());idx=old.index('-o');libs=old[idx+2:];resolved=[]
 for arg in libs:
  if not arg.startswith('-') and not Path(arg).is_absolute():arg=str((build/'vpr'/arg).resolve())
  resolved.append(arg)
 source=R/'tools/native_external_LUT_mask_v1.cpp';binary=out/'native_LUT_mask';cmd=['/usr/bin/c++','-std=c++17','-O2',*shlex.split(lines['CXX_DEFINES']),*shlex.split(lines['CXX_INCLUDES']),str(source),'-o',str(binary),*resolved];bindings={str(p):sha(p) for p in [source,flags,linkfile,Path(__file__).resolve(),*[Path(a) for a in resolved if a.endswith('.a')]]};(out/'build_protocol.json').write_text(json.dumps(dict(command=cmd,bindings=bindings,scope='Native library function harness only. No source copies, TilePlace writes, placement or routing.'),indent=2))
 with (out/'build.log').open('x') as log:result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 (out/'build_receipt.json').write_text(json.dumps(dict(exit_code=result.returncode,binary_sha256=sha(binary) if binary.exists() else None,bindings={str(out/'build_protocol.json'):sha(out/'build_protocol.json'),str(out/'build.log'):sha(out/'build.log')}),indent=2));print('NATIVE_LUT_BUILD_EXIT',result.returncode)
 if result.returncode:raise SystemExit(result.returncode)
if __name__=='__main__':main()
