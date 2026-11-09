"""All frozen placement candidates, native outcomes after predictor decision."""
import json,shutil,subprocess,time,os
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_swap_native_matrix_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_ram_comb_only_route_v1_2026-10-09';C=E/'full_ram_swap_candidates_v1_2026-10-09';proof=E/'full_ram_swap_decision_verification_v1_2026-10-09/verification.json'
v=json.loads(proof.read_text());assert v['passed']
for p,h in v['bindings'].items():assert sha(p)==h
p=json.loads((B/'protocol.json').read_text());command=p['command'];paths=[Path(__file__),proof,B/'protocol.json',Path(command[0]),Path(command[1]),*[B/n for n in ('design.blif','design.net','development.sdc')],B/'design.place',*[C/f'candidate_{i}/design.place' for i in (1,2)]];bindings={str(p):sha(p) for p in paths}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=command,cases=[0,1,2],selected_before_native=v['selected_candidate'],timeout_each_s=600,scope='All three frozen development placements, original comb-only route command except input place bytes. No stop-first-success or native-outcome-driven predictor selection. Independent product timing and Full physical initialization/equivalence unresolved.'),indent=2)+'\n')
results=[]
for i in (0,1,2):
 folder=D/f'candidate_{i}';folder.mkdir()
 for n in ('design.blif','design.net','development.sdc'):shutil.copyfile(B/n,folder/n)
 place=B/'design.place' if i==0 else C/f'candidate_{i}/design.place';shutil.copyfile(place,folder/'design.place');t=time.perf_counter()
 with (folder/'route.log').open('x') as log:
  try:code=subprocess.run(command,cwd=folder,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 row=dict(candidate=i,exit_code=code,native_s=time.perf_counter()-t,place_sha256=sha(folder/'design.place'),files={str(p):sha(p) for p in folder.iterdir() if p.is_file()});(folder/'receipt.json').write_text(json.dumps(row,indent=2)+'\n');results.append(row);print(i,code,row['native_s'],flush=True)
assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,results=results,scope='Native matrix complete; success requires independent route/placement audit, not merely exit code or file existence.'),indent=2)+'\n')
