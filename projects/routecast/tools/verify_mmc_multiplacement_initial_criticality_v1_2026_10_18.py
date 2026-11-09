"""Independent global-pin keyed TSV/manifest/float32 criticality replay."""
import json,sys,csv,struct,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_multiplacement_initial_criticality_v1_2026-10-18';vp=D/'verification.json';v=json.loads(vp.read_text());assert v['status']=='pass' and all(sha(p)==h for p,h in v['bindings'].items());bindings={**v['bindings'],**closure([Path(__file__)]),str(vp):sha(vp)};P=json.loads((D/'protocol.json').read_text());assert P['order']==['old','case_01','case_02','case_03'];oldsource=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10/initial_connection_criticalities.json';oldrecords=json.loads(oldsource.read_text());by_pin={x['global_pin']:x for x in oldrecords};assert len(by_pin)==115572;allpins=None;oldfloats=None;results=[]
for case in P['order']:
 W=D/case;src=Path(P['inputs'][case]['source']);assert not list(W.glob('*.route'));assert json.loads((W/'terminal.json').read_text())['exit_code']==0
 for name in ['design.net','design.blif','design.place']:assert sha(W/name)==sha(src/name)
 queries={}
 for line in Path(P['inputs'][case]['manifest']).open():
  cols=line.split()
  if cols[0]=='Q':
   cid,net,pin,source,sink=map(int,cols[1:]);assert (net,pin) not in queries;queries[net,pin]=(cid,source,sink)
 observed={};f32={};physical={};ignored=0
 with (W/'criticality.tsv').open(newline='') as stream:
  for seq,cols in enumerate(csv.reader(stream,delimiter='\t'),1):
   assert len(cols)==10 and cols[0]=='C' and int(cols[1])==seq;net,gpin,pin=map(int,cols[2:5]);assert gpin not in observed;ignoredflag=int(cols[8]);globalflag=int(cols[9]);assert ignoredflag in [0,1] and globalflag in [0,1];value=float(cols[5]);maximum=float(cols[6]);exponent=float(cols[7]);assert math.isfinite(value) and math.isfinite(maximum) and math.isfinite(exponent) and 0<=value<=maximum+1e-7;observed[gpin]=(net,pin,maximum,exponent,ignoredflag,globalflag);f32[gpin]=struct.pack('<f',value);ignored+=ignoredflag
   if not ignoredflag:
    assert gpin in by_pin and (net,pin) in queries;cid,source,sink=queries[net,pin];prior=by_pin[gpin];assert (cid,net,pin)==(prior['connection_id'],prior['net'],prior['local_sink_pin']);physical[gpin]=(cid,net,pin,source,sink,cols[5])
 assert len(observed)==119473 and ignored==3901 and set(physical)==set(by_pin) and len(queries)==115572
 exported=json.loads((W/'initial_connection_criticalities.json').read_text());assert len(exported)==115572 and len({x['connection_id'] for x in exported})==115572
 for x in exported:
  gp=x['global_pin'];cid,net,pin,source,sink,value=physical[gp];assert (x['connection_id'],x['net'],x['local_sink_pin'],x['source_rr'],x['target_rr'])==(cid,net,pin,source,sink);assert struct.pack('<f',float(x['criticality_float32_text']))==f32[gp] and float(x['maximum_text'])==observed[gp][2] and float(x['exponent_text'])==observed[gp][3]
 if case=='old':
  assert all(f32[gp]==struct.pack('<f',float(row['criticality_float32_text'])) for gp,row in by_pin.items());allpins=observed;oldfloats=f32
 else:assert observed==allpins
 changed={gp for gp in by_pin if f32[gp]!=oldfloats[gp]};nets={by_pin[gp]['net'] for gp in changed};dirty=set() if case=='old' else set(json.loads((src.parent/'staged_input_verification_v1.json').read_text())['affected']['affected_net_ids']);outside={gp for gp in changed if by_pin[gp]['net'] not in dirty};delta=[abs(float(physical[gp][5])-float(by_pin[gp]['criticality_float32_text'])) for gp in by_pin];mean=math.fsum(delta)/len(delta);row=next(x for x in v['rows'] if x['case']==case);assert row['changed_float32_criticalities']==len(changed) and row['changed_NETs']==len(nets) and row['changed_queries_outside_endpoint_closure']==len(outside) and row['changed_NETs_outside_endpoint_closure']==len(nets-dirty) and row['max_abs_criticality_delta']==max(delta) and math.isclose(row['mean_abs_criticality_delta'],mean,rel_tol=1e-12,abs_tol=1e-15)
 results.append(dict(case=case,physical_queries=115572,all_sink_pins=119473,changed_float32_criticalities=len(changed),changed_NETs=len(nets),changed_queries_outside_endpoint_closure=len(outside),changed_NETs_outside_endpoint_closure=len(nets-dirty),maximum_delta=max(delta),mean_delta=mean));print('INDEPENDENT CRITICALITY',results[-1],flush=True)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=results,all4_TSV_global_pin_manifest_and_float32_comparisons_independently_replayed=True,all4_inputs_unchanged_and_no_routes_generated=True,scope='Global-pin-keyed independent CSV/float32 arithmetic and manifest replay. Authenticated observer hooks establish pre-connection exit scope; no original-source-code proof of complete timing semantics, generalization, route acceptance or performance claim.'),f,indent=2)
