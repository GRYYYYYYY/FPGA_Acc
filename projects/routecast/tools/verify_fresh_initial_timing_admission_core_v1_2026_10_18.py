"""Fresh timing admission negative cases plus exact legacy/float32 parity."""
import json,sys,struct,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from load_initial_connection_criticalities_v1 import load as legacy
from load_initial_connection_criticalities_v2 import load
D=R/'experiments/fresh_initial_timing_admission_core_v1_2026-10-18';D.mkdir();results=[]
base=[dict(connection_id=i,net=i,local_sink_pin=1,global_pin=20+i,source_rr=10+2*i,target_rr=11+2*i,criticality_float32_text=x,maximum_text='0.99',exponent_text='1') for i,x in enumerate(['0.1','0.75'])]
def fixture(name):
 d=D/name;d.mkdir();(d/'case_01').mkdir();(d/'timing').mkdir();src=d/'case_01/initial_connection_criticalities.json';vec=d/'timing/initial_connection_criticalities.json';ep=d/'endpoints.json';ip=d/'independent.json';ap=d/'timing/verification.json'
 def write(p,obj):p.write_text(json.dumps(obj))
 write(src,base);write(vec,base);write(ep,dict(connections=[dict(connection_id=x['connection_id'],net_id=x['net'],source=x['source_rr'],sink=x['target_rr']) for x in base]));proof=dict(status='pass',bindings={str(src):sha(src),str(ep):sha(ep)},rows=[dict(case='case_01',physical_queries=2)],all4_TSV_global_pin_manifest_and_float32_comparisons_independently_replayed=True,all4_inputs_unchanged_and_no_routes_generated=True,test_fixture_only=True);write(ip,proof);admit=dict(schema='ROUTECAST_FRESH_INITIAL_TIMING_V1',bindings={str(src):sha(src),str(vec):sha(vec),str(ep):sha(ep),str(ip):sha(ip)},source_case='case_01',after_endpoint=str(ep),independent_snapshot_proof=str(ip),routed_connections=2,nonignored_pin_keys_exactly_manifest=True,fresh_float32_values_and_pin_identities_independently_verified=True,no_target_route_generated=True);write(ap,admit)
 return d,src,vec,ep,ip,ap,write
f=fixture('valid');out=load(f[0]/'timing');value=struct.unpack('f',struct.pack('f',0.1))[0];assert (out[0]['criticality_numerator'],out[0]['criticality_denominator'])==value.as_integer_ratio();results.append(dict(name='valid_exact_float32',pass_test=True))
mutations=['missing_fresh_flag','legacy_equality_claim','changed_payload_unbound','rebound_payload_not_source','wrong_endpoint_unbound','wrong_endpoint_rebound','unknown_case','wrong_case','failed_independent_proof','missing_independent_flag','unbound_independent_source','duplicate_CID','duplicate_NET_pin','nan_value','above_maximum','missing_row']
for name in mutations:
 d,src,vec,ep,ip,ap,write=fixture(name);a=json.loads(ap.read_text());p=json.loads(ip.read_text());rows=json.loads(vec.read_text())
 if name=='missing_fresh_flag':a.pop('fresh_float32_values_and_pin_identities_independently_verified')
 elif name=='legacy_equality_claim':a['all_values_and_pin_identities_equal_v1']=True
 elif name=='changed_payload_unbound':rows[0]['criticality_float32_text']='0.2';write(vec,rows)
 elif name=='rebound_payload_not_source':rows[0]['criticality_float32_text']='0.2';write(vec,rows);a['bindings'][str(vec)]=sha(vec)
 elif name.startswith('wrong_endpoint'):
  e=json.loads(ep.read_text());e['connections'][0]['source']=999;write(ep,e)
  if name.endswith('rebound'):p['bindings'][str(ep)]=sha(ep);write(ip,p);a['bindings'][str(ep)]=sha(ep);a['bindings'][str(ip)]=sha(ip)
 elif name=='unknown_case':a['source_case']='none'
 elif name=='wrong_case':a['source_case']='case_02'
 elif name=='failed_independent_proof':p['status']='fail';write(ip,p);a['bindings'][str(ip)]=sha(ip)
 elif name=='missing_independent_flag':p.pop('all4_inputs_unchanged_and_no_routes_generated');write(ip,p);a['bindings'][str(ip)]=sha(ip)
 elif name=='unbound_independent_source':p['bindings'].pop(str(src));write(ip,p);a['bindings'][str(ip)]=sha(ip)
 else:
  if name=='duplicate_CID':rows[1]['connection_id']=0
  elif name=='duplicate_NET_pin':rows[1]['net']=0
  elif name=='nan_value':rows[0]['criticality_float32_text']='nan'
  elif name=='above_maximum':rows[0]['criticality_float32_text']='1.0'
  elif name=='missing_row':rows.pop()
  write(src,rows);write(vec,rows);p['bindings'][str(src)]=sha(src);write(ip,p);a['bindings'].update({str(src):sha(src),str(vec):sha(vec),str(ip):sha(ip)})
 write(ap,a)
 try:load(d/'timing')
 except (ValueError,KeyError,FileNotFoundError) as exc:results.append(dict(name=name,rejected=True,error_type=type(exc).__name__))
 else:raise AssertionError('accepted '+name)
d=D/'legacy';d.mkdir();vec=d/'initial_connection_criticalities.json';vec.write_text(json.dumps(base));(d/'verification.json').write_text(json.dumps(dict(bindings={str(vec):sha(vec)},nonignored_pin_keys_exactly_manifest=True,all_values_and_pin_identities_equal_v1=True,routed_connections=2)));assert dict(load(d))==dict(legacy(d));results.append(dict(name='legacy_exact_parity',pass_test=True))
with (D/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=closure([Path(__file__)]),results=results,rejections=len(mutations),scope='Synthetic admission/float32/legacy parity only; fixtures explicitly do not constitute native evidence. Production needs the already independently replayed real native snapshot proof.'),f,indent=2)
print('PASS fresh admission:16 rejection cases, float32 and legacy parity',flush=True)
