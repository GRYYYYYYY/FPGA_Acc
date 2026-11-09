"""Serial zero-feedback cold parity and same-placement loaded-seed trial."""
import json,os,shutil,subprocess,time
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2]
build=ROOT/'build/native_resume_branch_partial_v8_2026-10-08';br=json.loads((build/'receipt.json').read_text());binary=build/'routecast_resume_vpr';assert sha(binary)==br['binary_sha256']
prior=ROOT/'experiments/mux32_old_placement_cold_control_2026-10-07';p=json.loads((prior/'protocol.json').read_text());r=json.loads((prior/'receipt.json').read_text());assert all(sha(f)==h for f,h in p['inputs'].items())
source=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128';seed=ROOT/'experiments/fresh_retained_branch_seed_v3_2026-10-08/w32_m2.route'
target_place=ROOT/'experiments/mux_budget_move_cohort_2026-10-06/w32_m2/target.place'
partial_receipt=seed.parent/'receipt.json'
assert sha(seed)==next(x['route_sha256'] for x in json.loads(partial_receipt.read_text())['rows'] if x['width']==32 and x['index']==2)
proof_path=seed.parent/'verification.json';proof=json.loads(proof_path.read_text());assert proof['exact_native_trace_and_certified_sink_identity_byte_equality_pass'] and all(sha(path)==digest for path,digest in proof['bindings'].items())
out=ROOT/'experiments/fresh_retained_branch_resume_v3_2026-10-08';out.mkdir(exist_ok=False)
protocol=dict(build_receipt_sha256=sha(build/'receipt.json'),trial_source_sha256=sha(Path(__file__)),inputs={str(f):sha(f) for f in (seed,source/'design.blif',source/'design.net',source/'design.place',prior/'output.route',target_place,partial_receipt)},scope='Target w32/m2 budget-filtered branch-partial resume; missing sink delay1ns heuristic; component-only native clock excludes base/serialization/audits, no end-to-end gain or quality guarantee')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
norm=lambda f:{name:Counter(paths) for name,paths in physical_paths(f).items() if paths}
for mode in ('resume',):
 work=out/mode;work.mkdir()
 for name in ('design.blif','design.net','design.place'):shutil.copyfile(source/name,work/name)
 shutil.copyfile(target_place,work/'design.place')
 cmd=[str(binary),*r['command'][1:]];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 if mode=='resume':env['ROUTECAST_RESUME_SAME_PLACE_ROUTE']=str(seed);env['ROUTECAST_RESUME_ALLOW_PARTIAL']='1';env['ROUTECAST_RESUME_ALLOW_BRANCH_PARTIAL']='1'
 start=time.perf_counter()
 with (work/'run.log').open('w') as log:code=subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
 text=(work/'run.log').read_text();route=work/'output.route'
 row=dict(mode=mode,exit_code=code,wall_seconds=time.perf_counter()-start,command=cmd,log_sha256=sha(work/'run.log'),loaded_tree_marker='ROUTECAST_RESUME_LOADED_TREES' in text,first_tree_markers=text.count('ROUTECAST_RESUME_FIRST_TREE'),full_check='Completed routing consistency check successfully.' in text,vpr_succeeded='VPR succeeded' in text,route_sha256=sha(route) if route.exists() else None)
 if code==0:
  row['cold_path_parity']=norm(route)==norm(prior/'output.route')
  row['seed_path_parity']=norm(route)==norm(seed)
 if mode=='cold':assert code==0 and row['cold_path_parity'] and not row['loaded_tree_marker']
 rows.append(row)
assert all(sha(f)==h for f,h in protocol['inputs'].items())
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,scope=protocol['scope']),indent=2)+'\n');print(rows)
