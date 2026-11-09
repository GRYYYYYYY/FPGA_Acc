import json,os,re,shutil,subprocess
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_retained_phase_cost_2026-10-06';out.mkdir();work=root/'work/native_candidate_retained_phase_cost_2026-10-06';work.mkdir();results=[]
for label,parent,count in [('multiplier','native_candidate_multi_pair_2026-10-06',129),('adder','native_candidate_adder_sequence_2026-10-06',516)]:
 prior=root/'experiments'/parent;v=json.loads((prior/'verification.json').read_text());assert all(sha(f)==h for f,h in v['sha256'].items());r=json.loads((prior/'receipt.json').read_text());cmd=r['command'].copy();cmd[0]=str(root/'build/native_candidate_retained_phase_cost_2026-10-06/sequence_vpr');graph=cmd[cmd.index('--read_rr_graph')+1];source=root/'work'/parent/'single';cwd=work/label;cwd.mkdir();case=out/label;case.mkdir()
 for f in ('design.blif','design.net','design.place','seed.route'):shutil.copyfile(source/f,cwd/f)
 inputs={str(f):sha(f) for f in cwd.iterdir()};env=os.environ.copy();env.update(ROUTECAST_NATIVE_SEED=str(cwd/'seed.route'),ROUTECAST_TIMING_RESTORE_PROBE='1',ROUTECAST_MOVE_SEQUENCE='AAAA',ROUTECAST_MOVE_PAIRS='0 1 2 3 1 2 0 4')
 with (case/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
 assert code==0 and all(sha(f)==h for f,h in inputs.items());log=(case/'run.log').read_text();base=float(re.search(r'synchronized baseline CPD=([0-9.]+)',log)[1]);final=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1]);assert final<=base+1e-5
 a_count=log.count('accepted actual moved candidate after FULL check, packing sync and STA');r_count=log.count('restored delay matrix and all edge-delay/STA metric observations');assert a_count+r_count==4
 for path in [cwd/'output.route',*cwd.glob('candidate_*.route')]:
  a=audit(graph,path);assert len(a['connections'])==count and a['overflow_units']==0;(case/(path.stem+'_audit.json')).write_text(json.dumps(a,indent=2)+'\n')
 assert 'Placement_ID: SHA256:'+sha(cwd/'accepted.place') in (cwd/'output.route').read_text().splitlines()[0]
 results.append({'design':label,'exit_code':code,'baseline_cpd_ns':base,'final_cpd_ns':final,'accepted':a_count,'rejected':r_count,'inputs_sha256':inputs,'route_sha256':sha(cwd/'output.route'),'packed_sha256':sha(cwd/'design.net.post_routing'),'log_sha256':sha(case/'run.log'),'command':cmd});print(label,base,final,a_count,r_count,flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'binary_sha256':sha(cmd[0]),'scope':'Real CPD non-increase gate on four predefined pairs, synchronized baseline; previously used families, cold candidates. Not prediction-guided or full-pipeline speed evidence.'},indent=2)+'\n')
