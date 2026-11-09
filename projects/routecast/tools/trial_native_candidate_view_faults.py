import json,os,subprocess,shutil
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_view_faults_2026-10-06';out.mkdir();work=root/'work/native_candidate_view_faults_2026-10-06';work.mkdir();parent=root/'experiments/native_candidate_sequence_views_2026-10-06';v=json.loads((parent/'verification.json').read_text());assert all(sha(f)==h for f,h in v['sha256'].items());receipt=json.loads((parent/'receipt.json').read_text());gold={r['sequence']:r for r in receipt['results']};cmd=receipt['command'];cmd[0]=str(root/'build/native_candidate_view_faults_2026-10-06/sequence_vpr');graph=cmd[cmd.index('--read_rr_graph')+1];source=root/'work/native_candidate_sequence_views_2026-10-06/A';results=[]
for sequence in ('AR','ARA'):
 for kind in ('runtime_error','bad_alloc'):
  for stage in (1,2,3):
   name=f'{sequence}_{kind}_{stage}';cwd=work/name;cwd.mkdir();case=out/name;case.mkdir()
   for f in ('design.blif','design.net','design.place','seed.route'):shutil.copyfile(source/f,cwd/f)
   inputs={str(f):sha(f) for f in cwd.iterdir()};env=os.environ.copy();env.update(ROUTECAST_NATIVE_SEED=str(cwd/'seed.route'),ROUTECAST_TIMING_RESTORE_PROBE='1',ROUTECAST_MOVE_SEQUENCE=sequence,ROUTECAST_VIEW_FAULT_STAGE=str(stage));env.pop('ROUTECAST_VIEW_FAULT_BAD_ALLOC',None)
   if kind=='bad_alloc':env['ROUTECAST_VIEW_FAULT_BAD_ALLOC']='1'
   with (case/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
   assert code==0 and all(sha(f)==h for f,h in inputs.items());log=(case/'run.log').read_text();assert f'injected view-copy fault step=1 stage={stage}' in log and 'restored delay matrix and all edge-delay/STA metric observations' in log
   reference='A' if sequence=='AR' else 'AA'
   for f in ('output.route','design.net.post_routing','accepted.place'):assert (cwd/f).read_bytes()==(root/'work/native_candidate_sequence_views_2026-10-06'/reference/f).read_bytes()
   paths=[cwd/'output.route',*cwd.glob('candidate_*.route')];assert len(paths)==len(sequence)
   for path in paths:
    a=audit(graph,path);assert len(a['connections'])==129 and a['overflow_units']==0;(case/(path.stem+'_audit.json')).write_text(json.dumps(a,indent=2)+'\n')
   results.append({'case':name,'exit_code':code,'reference':reference,'inputs_sha256':inputs,'log_sha256':sha(case/'run.log'),'route_sha256':sha(cwd/'output.route'),'packed_sha256':sha(cwd/'design.net.post_routing'),'audited_routes':len(paths)});print(name,'pass',flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'command':cmd,'binary_sha256':sha(cmd[0]),'scope':'Injected checkpoint exceptions during canonical view copies, after an accepted move; exact prefix restoration and later candidate acceptance. Not actual allocator exhaustion, allocation-free recovery, or production exception policy.'},indent=2)+'\n')
