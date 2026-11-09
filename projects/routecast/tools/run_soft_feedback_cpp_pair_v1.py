"""Serial current-process component comparison; fixed order, no native performance claim."""
import sys,json,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/soft_feedback_cpp_pair_v1_2026-10-07';out.mkdir();cpp=R/'tools/trial_soft_demand_feedback_cpp_v2.py';py=R/'tools/trial_soft_demand_feedback_python_replay_v1.py';existing=R/'experiments/mcnc_soft_demand_feedback_cpp_v2_2026-10-07/misex3/receipt.json';assert existing.exists();sources={**closure([cpp,py,Path(__file__)]),str(R/'experiments/soft_demand_cpp_build_v1_2026-10-07/search.so'):sha(R/'experiments/soft_demand_cpp_build_v1_2026-10-07/search.so'),str(existing):sha(existing)};order=[('misex3','python'),('bigkey','cpp'),('bigkey','python'),('dsip','python'),('dsip','cpp')];(out/'protocol.json').write_text(json.dumps(dict(bindings=sources,order=order,scope='Current serial process comparison of exact same two-round feedback workload, including RC loading/conversion, array setup, per-event full ledger assertions, output serialization and binding verification. First misex3 C++ run completed before this timing protocol, reported explicitly; other five runs frozen now. Not repeated/statically controlled hardware benchmark; initial prediction, floors, compile, independent auditing and native final routing excluded, no end-to-end/net-gain claim.'),indent=2)+'\n');rows=[]
for name,backend in order:
 start=time.perf_counter();log=out/f'{name}_{backend}.log';script=cpp if backend=='cpp' else py
 with log.open('w') as stream:status=subprocess.run([sys.executable,str(script),name],cwd=R,stdout=stream,stderr=subprocess.STDOUT).returncode
 row=dict(name=name,backend=backend,exit_code=status,child_wall_seconds=time.perf_counter()-start,log=str(log));rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('SERIAL COMPONENT',row,flush=True)
 if status:raise RuntimeError('Stopped on component failure; no successful timing comparison claim')
assert all(sha(k)==h for k,h in sources.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=sources,rows=rows,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n')
