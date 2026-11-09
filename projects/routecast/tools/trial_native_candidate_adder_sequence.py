import json,os,shutil,subprocess,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_candidate_adder_sequence_2026-10-06';out.mkdir();work=root/'work/native_candidate_adder_sequence_2026-10-06';work.mkdir()
parent=root/'experiments/adder_tree_family_native_capture_v2_2026-10-06';prior=json.loads((parent/'adder_tree_2L_032bits_receipt.json').read_text());assert prior['exit_code']==0 and all(sha(x['path'])==x['sha256'] for x in prior['artifacts'].values())
command=json.loads((parent/'adder_tree_2L_032bits_command.json').read_text());source=Path(command['cwd']);graph=str(source/'rr_graph.xml');binary=root/'build/native_candidate_multi_pair_2026-10-06/sequence_vpr';cmd=[str(binary),command['command'][1],'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',graph,'--route_chan_width','300','--num_workers','1'];results=[]
for name,sequence,pairs in [('single','A','0 1'),('two','AA','0 1 2 3'),('two_reject','AAR','0 1 2 3 1 4'),('overlap','AAA','0 1 2 3 1 2'),('overlap_reject','AAAR','0 1 2 3 1 2 0 4')]:
 cwd=work/name;cwd.mkdir();case=out/name;case.mkdir()
 for filename in ('design.blif','design.net','design.place'):shutil.copyfile(source/filename,cwd/filename)
 shutil.copyfile(source/'design.route',cwd/'seed.route')
 inputs={str(f):sha(f) for f in cwd.iterdir()};env=os.environ.copy();env.update(ROUTECAST_NATIVE_SEED=str(cwd/'seed.route'),ROUTECAST_TIMING_RESTORE_PROBE='1',ROUTECAST_MOVE_SEQUENCE=sequence,ROUTECAST_MOVE_PAIRS=pairs);env.pop('ROUTECAST_SYNC_TICKET_FAULT',None)
 with (case/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
 assert all(sha(f)==h for f,h in inputs.items());result={'case':name,'pairs':pairs,'sequence':sequence,'exit_code':code,'inputs_sha256':inputs,'log_sha256':sha(case/'run.log')}
 if code==0:
  log=(case/'run.log').read_text();assert len(re.findall('ROUTECAST sequence step=',log))==len(sequence)
  for path in [cwd/'output.route',*sorted(cwd.glob('candidate_*.route'))]:
   a=audit(graph,path);assert len(a['connections'])==516 and a['overflow_units']==0;(case/(path.stem+'_audit.json')).write_text(json.dumps(a,indent=2)+'\n')
  result.update(route_sha256=sha(cwd/'output.route'),packed_sha256=sha(cwd/'design.net.post_routing'),cpd_ns=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1]))
  assert 'Placement_ID: SHA256:'+sha(cwd/'accepted.place') in (cwd/'output.route').read_text().splitlines()[0]
 results.append(result);print(sequence,code,flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'command':cmd,'binary_sha256':sha(cmd[0]),'scope':'Actual serial candidate moves and packing sync/STA in same native process, fixed pair; external reconstruction not used between steps.'},indent=2)+'\n')
