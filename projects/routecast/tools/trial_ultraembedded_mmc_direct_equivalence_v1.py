"""Full original MMC HDL versus archived synthesis, direct SAT attempt."""
import json,sys,subprocess,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/ultraembedded_mmc_direct_equivalence_v1_2026-10-08';out.mkdir()
front=R/'experiments/ultraembedded_peripheral_frontends_v1_2026-10-08/mmc'
source=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/benchmarks/ultraembedded/mmc_core.v'
availability=R/'experiments/prospective_family_candidates_2026-10-06/frontend_availability.json';tool=json.loads(availability.read_text());binary=Path(tool['yosys_path']);assert sha(binary)==tool['sha256'];assert source.read_bytes()==(front/'design.v').read_bytes()
shutil.copyfile(source,out/'original.v');shutil.copyfile(front/'design.json',out/'gate.json')
script=out/'equivalence.ys';script.write_text('read_verilog original.v\nhierarchy -check -top mmc_card\nproc\nflatten\nmemory_map\nopt\ntechmap\nopt\nrename mmc_card gold\ndesign -stash gold\nread_json gate.json\nrename mmc_card gate\ndesign -stash gate\ndesign -copy-from gold -as gold gold\ndesign -copy-from gate -as gate gate\nequiv_make gold gate equiv\nhierarchy -check -top equiv\nwrite_json before.json\nequiv_simple -undef\nwrite_json after.json\nequiv_status -assert\n')
files=[Path(__file__),source,front/'design.v',front/'design.json',availability,binary,out/'original.v',out/'gate.json',script];bindings={str(p):sha(p) for p in files};cmd=[str(binary),'-Q','-T','-s','equivalence.ys']
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=cmd,timeout_seconds=600,scope='Full unchanged original HDL/FIFO/all ports, archived gate JSON. Fresh gold proc/flatten/memory_map/techmap, direct SAT with undef. No async2sync/reset assumptions/induction/port projections/blacklists. Failed or unproven remains open; even tool PASS needs independent scope audit for initialization/asynchronous semantics.'),indent=2)+'\n')
tick=time.perf_counter();status='UNVERIFIED';error=None;exit_code=None
try:
 with (out/'equivalence.log').open('w') as f:r=subprocess.run(cmd,cwd=out,stdout=f,stderr=subprocess.STDOUT,timeout=600)
 exit_code=r.returncode;status='TOOL_STATUS_PASS_PENDING_SCOPE_AUDIT' if exit_code==0 else 'FAILED_OR_UNPROVEN'
except subprocess.TimeoutExpired as e:status='TIMEOUT';error=repr(e)
assert all(sha(k)==h for k,h in bindings.items())
result=dict(bindings=bindings,status=status,exit_code=exit_code,error=error,elapsed_seconds=time.perf_counter()-tick,files={str(p):sha(p) for p in out.iterdir() if p.is_file()},original_hdl_complete_equivalence_proven=False,scope='Attempt receipt only. No success inferred from wrapper exit or partial SAT proofs; independent all-point/port/state/asynchronous/initial-state coverage audit required.')
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(status,exit_code,flush=True)
