"""Prepared complete 3-move transaction/native cohort ABBA, not cold synthesis."""
import os,json,subprocess,time,shutil
from pathlib import Path
from pre_route_endpoints import sha

root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'cpp_transactional_rc_native_pipeline_2026-10-06';work=root/'work/cpp_transactional_rc_native_pipeline_2026-10-06';out.mkdir();work.mkdir()
sequence=base/'adder_tree_2L032_move_sequence_2026-10-06';inputs=json.loads((sequence/'protocol.json').read_text())['inputs'];binary=root/'build/native_pressure_feedback_v2_2026-10-06/routecast_pressure_vpr';build=json.loads((binary.parent/'receipt.json').read_text());assert sha(binary)==build['binary_sha256'];assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
protocol={'inputs':inputs,'binary_sha256':sha(binary),'source_sha256':{n:sha(root/'tools'/n) for n in ['benchmark_cpp_transactional_rc_native_pipeline.py','run_native_transactional_rc_move_sequence.py']},'order':['off','on','on','off'],'scope':'Full three preselected consecutive moves. On fresh subprocess reads/authenticates prepared CSR/RC and verified initial snapshot, performs all move repair/RC search/transaction/final validation/audit/export, then 3 native cold routes. Off 3 same-placement native cold routes only. HDL/RR/CSR/electrical/budget preparation and initial accepted prediction generation excluded, but their loading/authentication in driver charged. Common immutable native staging outside, logs/env/native loop inside. No fault injection during timing.'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for trial,mode in enumerate(protocol['order']):
 staged=[]
 for step in range(1,4):
  wd=work/f'{trial}_{mode}_{step}';wd.mkdir()
  shutil.copyfile(inputs['atom']['path'],wd/'design.blif');shutil.copyfile(inputs['packed_netlist']['path'],wd/'design.net');shutil.copyfile(sequence/f'step_{step}.place',wd/'design.place');staged.append(wd)
 fresh=base/f'cpp_transactional_rc_pipeline_fresh_{trial}_2026-10-06'
 start=time.monotonic();driver_s=0
 if mode=='on':
  env=dict(os.environ,PYTHONPATH=str(root/'tools'),ROUTECAST_TRANSACTION_OUTPUT=str(fresh));env.pop('ROUTECAST_INJECT_FAILURES',None);t=time.monotonic()
  with (out/f'{trial}_driver.log').open('w') as log:code=subprocess.run(['python3','-u',str(root/'tools/run_native_transactional_rc_move_sequence.py')],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
  assert code==0;driver_s=time.monotonic()-t
 native=[]
 for step,wd in enumerate(staged,1):
  env=dict(os.environ)
  for key in ('ROUTECAST_PRESSURE_FILE','ROUTECAST_EXPECT_GRAPH_SHA256'):env.pop(key,None)
  if mode=='on':env['ROUTECAST_PRESSURE_FILE']=str(fresh/f'step_{step}.pressure');env['ROUTECAST_EXPECT_GRAPH_SHA256']=inputs['rr_graph']['sha256']
  command=[str(binary),inputs['architecture']['path'],'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',inputs['rr_graph']['path'],'--route_chan_width','300','--num_workers','1','--seed','1','--max_router_iterations','100'];t=time.monotonic();logfile=out/f'{trial}_{mode}_{step}.log'
  with logfile.open('w') as log:code=subprocess.run(command,cwd=wd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
  elapsed=time.monotonic()-t;assert code==0;native.append({'step':step,'native_s':elapsed,'route_path':str(wd/'design.route'),'log_path':str(logfile)})
 elapsed=time.monotonic()-start
 row={'trial':trial,'mode':mode,'full_prepared_pipeline_s':elapsed,'driver_s':driver_s,'native':native,'fresh_output':str(fresh) if mode=='on' else None};rows.append(row);print(json.dumps({k:row[k] for k in ['trial','mode','full_prepared_pipeline_s','driver_s']}),flush=True)
assert all(sha(root/'tools'/n)==h for n,h in protocol['source_sha256'].items());assert sha(binary)==protocol['binary_sha256'];assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'runs':rows},indent=2)+'\n')
