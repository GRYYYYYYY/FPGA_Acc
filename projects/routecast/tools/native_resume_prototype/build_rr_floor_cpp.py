import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];source=Path(__file__).with_name('rr_floor_cpp')/'main.cpp';out=ROOT/'build/native_resume_rr_floor_cpp_2026-10-07';out.mkdir(exist_ok=False);binary=out/'rr_floor';cmd=['c++','-std=c++17','-O3','-Wall','-Wextra',str(source),'-o',str(binary)]
with (out/'compile.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
(out/'receipt.json').write_text(json.dumps(dict(source=str(source),source_sha256=sha(source),binary=str(binary),binary_sha256=sha(binary),command=cmd),indent=2)+'\n');print(binary)
