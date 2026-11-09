"""Fixed six-case ABBA native feedback development trial, failures retained."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from prepared_csr import read
from incremental_channel_pressure import ChannelPressure
from stream_native_route_audit import audit


def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_corridor_pressure_trial_2026-10-06';out.mkdir();work=root/'work/multiplier_cw32_corridor_pressure_trial_2026-10-06';work.mkdir(parents=True);(out/'sources').mkdir()
 names=['trial_multiplier_cw32_corridor_pressure.py','incremental_channel_pressure.py','prepared_csr.py','stream_native_route_audit.py','audit_native_route.py','pre_route_endpoints.py']
 for n in names:shutil.copyfile(root/'tools'/n,out/'sources'/n)
 binary=root/'build/native_pressure_feedback_v2_2026-10-06/routecast_pressure_vpr';br=json.loads((binary.parent/'receipt.json').read_text());assert sha(binary)==br['binary_sha256']
 sequence=['off','on','on','off'];protocol={'cohort':[f'mult_{w}x{w}' for w in range(4,10)],'sequence':sequence,'sources':{n:sha(out/'sources'/n) for n in names},'binary_sha256':sha(binary),'width':32,'seed':1,'workers':1,'max_iterations':100,'timeout_s':120,'formula':'CHANX/Y only: 1+max(predicted unique-net occupancy-capacity,0)/capacity, coefficient1, same existing exact-track rule','scope':'Complete exposed development cohort at fixed captured place and graph. Precomputed prediction; payload generation separate. Native timed only, no full-pipeline gain or unseen claim.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');allrows=[]
 for name in protocol['cohort']:
  dest=out/name;dest.mkdir();front=root/'experiments/multiplier_family_endpoints_cw32_2026-10-06'/name;fp=json.loads((front/'protocol.json').read_text());fr=json.loads((front/'receipt.json').read_text());assert sha(front/'protocol.json')==fr['protocol_sha256'];inputs=fp['inputs'];assert all(sha(v['path'])==v['sha256'] for v in inputs.values());assert all(sha(front/n)==h for n,h in fr['outputs'].items())
  predroot=root/'experiments/multiplier_cw32_scalar_corridor_admission_2026-10-06'/name;parent=predroot.parent;parent_receipt=json.loads((parent/'receipt.json').read_text());pr=next(r for r in parent_receipt['results'] if r['design']==name);assert sha(predroot/'prediction.json')==pr['prediction_sha256'];assert sha(predroot/'audit.json')==pr['audit_sha256'];aroot=predroot;ar=json.loads((predroot/'audit.json').read_text());assert ar['all_physical_and_union_checks_passed'];assert pr['rejected_nets']==0
  quality=root/'experiments/multiplier_cw32_scalar_corridor_quality_2026-10-06';qr=json.loads((quality/'receipt.json').read_text());q=next(r for r in qr['results'] if r['design']==name);assert q['scalar_increased']==q['rc_increased']==0
  searchroot=root/'experiments/multiplier_cw32_scalar_corridor_2026-10-06';search_receipt=json.loads((searchroot/'receipt.json').read_text());search=next(r for r in search_receipt['results'] if r['design']==name)
  prepared=root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name;start=time.monotonic();m,f=read(prepared/'csr',inputs['rr_graph']['sha256']);pred=json.loads((predroot/'prediction.json').read_text());assert pred['physical_graph_sha256']==inputs['rr_graph']['sha256'];cache=ChannelPressure(f['types'],f['capacities']);cache.refresh({int(k):v for k,v in pred['node_occupancy'].items()},map(int,pred['node_occupancy']));payload=dest/'candidate.pressure';payload.write_text(cache.payload(inputs['rr_graph']['sha256']));payload_s=time.monotonic()-start
  ep=json.loads((front/'endpoints.json').read_text());expected=Counter((r['net_id'],r['source'],r['sink']) for r in ep['connections']);nets={r['net_id'] for r in ep['connections']}
  cp={'inputs':inputs,'endpoint_receipt_sha256':sha(front/'receipt.json'),'prediction_receipt_sha256':sha(parent/'receipt.json'),'prediction_audit_receipt_sha256':sha(predroot/'audit.json'),'pressure_sha256':sha(payload),'pressure_rows':len(cache.rows),'payload_generation_including_csr_auth_s':payload_s,'archived_full_prediction_s':search['wall_s']};(dest/'inputs.json').write_text(json.dumps(cp,indent=2)+'\n');rows=[]
  for i,mode in enumerate(sequence):
   tag=f'{i:02d}_{mode}';wd=work/name/tag;wd.mkdir(parents=True)
   for key,filename in [('atom','design.blif'),('packed_netlist','design.net'),('reference_place','design.place')]:shutil.copyfile(inputs[key]['path'],wd/filename)
   env=dict(os.environ)
   for key in ('ROUTECAST_PRESSURE_FILE','ROUTECAST_EXPECT_GRAPH_SHA256'):env.pop(key,None)
   if mode=='on':env.update(ROUTECAST_PRESSURE_FILE=str(payload),ROUTECAST_EXPECT_GRAPH_SHA256=inputs['rr_graph']['sha256'])
   cmd=[str(binary),inputs['architecture']['path'],'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',inputs['rr_graph']['path'],'--route_chan_width','32','--num_workers','1','--seed','1','--max_router_iterations','100'];(dest/(tag+'_command.json')).write_text(json.dumps({'command':cmd,'cwd':str(wd)},indent=2)+'\n');start=time.monotonic();timeout=False
   with (dest/(tag+'.log')).open('w') as log:
    try:code=subprocess.run(cmd,cwd=wd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
    except subprocess.TimeoutExpired:code=None;timeout=True
   elapsed=time.monotonic()-start;text=(dest/(tag+'.log')).read_text();assert ('RouteCast pressure applied' in text)==(mode=='on')
   if mode=='on':assert f'RouteCast pressure applied: {len(cache.rows)} channel nodes' in text
   success=code==0 and 'VPR succeeded' in text
   if not timeout:assert success or (code==2 and 'Circuit is unroutable' in text)
   physical_pass=None
   if success:
    phys=audit(inputs['rr_graph']['path'],wd/'design.route');actual=Counter((r['net_id'],r['source'],r['sink']) for r in phys['connections'] if r['net_id'] in nets);assert actual==expected and phys['overflow_units']==0
    header=(wd/'design.route').read_text().splitlines()[0];assert inputs['reference_place']['sha256'] in header
    (dest/(tag+'_physical.json')).write_text(json.dumps(phys)+'\n');physical_pass=True
   def metric(pattern,cast):
    match=re.search(pattern,text);return cast(match[1]) if match else None
   row={'design':name,'run':i,'mode':mode,'exit_code':code,'timeout':timeout,'native_route_s':elapsed,'success':success,'independent_physical_pass':physical_pass,'iterations':metric(r'Successfully routed after (\d+) routing iterations',int),'final_overused_nodes':metric(r'Total number of overused nodes: (\d+)',int),'cpd_ns':metric(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',float) if success else None,'wirelength':metric(r'Total wirelength:\s*(\d+)',int) if success else None,'log_sha256':sha(dest/(tag+'.log')),'route_sha256':sha(wd/'design.route') if (wd/'design.route').exists() else None};rows.append(row);allrows.append(row);print(json.dumps(row),flush=True)
   (dest/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
  assert sha(payload)==cp['pressure_sha256'] and all(sha(v['path'])==v['sha256'] for v in inputs.values());(dest/'receipt.json').write_text(json.dumps({'inputs_sha256':sha(dest/'inputs.json'),'rows':rows},indent=2)+'\n')
 assert all(sha(root/'tools'/n)==h for n,h in protocol['sources'].items()) and sha(binary)==protocol['binary_sha256'];(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':allrows,'case_receipts':{n:sha(out/n/'receipt.json') for n in protocol['cohort']}},indent=2)+'\n')
if __name__=='__main__':main()
