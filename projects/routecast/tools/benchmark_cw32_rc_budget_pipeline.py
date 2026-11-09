"""Full six-case prepared-context ABBA pipeline, no cold-input cost claim."""
import json,os,subprocess,shutil,time
from pathlib import Path
from pre_route_endpoints import sha
from prepared_csr import read
from incremental_channel_pressure import ChannelPressure

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_rc_budget_pipeline_2026-10-06';out.mkdir();work=root/'work/multiplier_cw32_rc_budget_pipeline_2026-10-06';work.mkdir(parents=True);cohort=[f'mult_{w}x{w}' for w in range(4,10)];previous=root/'experiments/multiplier_cw32_rc_budget_pressure_trial_2026-10-06';sources={n:sha(root/'tools'/n) for n in ('benchmark_cw32_rc_budget_pipeline.py','search_cw32_rc_budgeted_nets_timed.py','incremental_channel_pressure.py')};protocol={'cohort':cohort,'sequence':['off','on','on','off'],'sources':sources,'scope':'Prepared-context full cohort time includes on fresh search driver auth/index/search/RC budget/wholeNET state/output/independent path audit, pressure CSR auth/export and native routing; immutable staging and per-run command/log setup shared and outside. Cold frontend/RR/CSR/electrical preparation excluded. On prediction consumes no native results.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
 for i,mode in enumerate(protocol['sequence']):
  block=out/f'{i:02d}_{mode}';block.mkdir();commands={};inputs_by={}
  for name in cohort:
   prior=previous/name;inp=json.loads((prior/'inputs.json').read_text())['inputs'];assert all(sha(v['path'])==v['sha256'] for v in inp.values());inputs_by[name]=inp;wd=work/f'{i:02d}_{mode}'/name;wd.mkdir(parents=True)
   for key,filename in [('atom','design.blif'),('packed_netlist','design.net'),('reference_place','design.place')]:shutil.copyfile(inp[key]['path'],wd/filename)
   commands[name]=json.loads((prior/'00_off_command.json').read_text())['command']
  start=time.monotonic();search_s=0;predictionroot=block/'fresh_prediction'
  if mode=='on':
   env=dict(os.environ,PYTHONPATH=str(root/'tools'),ROUTECAST_FRESH_OUTPUT=str(predictionroot));t=time.monotonic()
   with (block/'search.log').open('w') as log:code=subprocess.run(['python3',str(root/'tools/search_cw32_rc_budgeted_nets_timed.py')],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
   assert code==0;search_s=time.monotonic()-t
  rows=[]
  for name in cohort:
   inp=inputs_by[name];wd=work/f'{i:02d}_{mode}'/name;env=dict(os.environ)
   for k in ('ROUTECAST_PRESSURE_FILE','ROUTECAST_EXPECT_GRAPH_SHA256'):env.pop(k,None)
   payload_s=0
   if mode=='on':
    t=time.monotonic();predfile=predictionroot/name/'prediction.json';r=json.loads((predictionroot/name/'receipt.json').read_text());assert sha(predfile)==r['prediction_sha256'];pred=json.loads(predfile.read_text());m,f=read(root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name/'csr',inp['rr_graph']['sha256']);cache=ChannelPressure(f['types'],f['capacities']);occ={int(n):v for n,v in pred['node_occupancy'].items()};cache.refresh(occ,occ);payload=block/(name+'.pressure');payload.write_text(cache.payload(inp['rr_graph']['sha256']));assert payload.read_bytes()==(previous/name/'candidate.pressure').read_bytes();env.update(ROUTECAST_PRESSURE_FILE=str(payload),ROUTECAST_EXPECT_GRAPH_SHA256=inp['rr_graph']['sha256']);payload_s=time.monotonic()-t
   t=time.monotonic();logfile=block/(name+'.log')
   with logfile.open('w') as log:code=subprocess.run(commands[name],cwd=wd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
   native_s=time.monotonic()-t;assert code in (0,2);route=wd/'design.route';reference=json.loads((previous/name/'receipt.json').read_text());old=next(x for x in reference['rows'] if x['mode']==mode);assert code==old['exit_code'] and sha(route)==old['route_sha256'];rows.append({'design':name,'exit_code':code,'success':code==0,'payload_s':payload_s,'native_s':native_s,'route_sha256':sha(route),'log_sha256':sha(logfile),'reference_receipt_sha256':sha(previous/name/'receipt.json')})
  row={'run':i,'mode':mode,'cohort_pipeline_s':time.monotonic()-start,'fresh_search_driver_s':search_s,'cases':rows};results.append(row);(block/'receipt.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps({k:row[k] for k in ('run','mode','cohort_pipeline_s','fresh_search_driver_s')}),flush=True)
 assert all(sha(root/'tools'/n)==h for n,h in sources.items());means={mode:sum(r['cohort_pipeline_s'] for r in results if r['mode']==mode)/2 for mode in ('off','on')};(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':results,'means':means,'on_over_off':means['on']/means['off'],'all_actual_routes_match_independently_audited_prior':True},indent=2)+'\n');print(json.dumps(means),flush=True)
if __name__=='__main__':main()
