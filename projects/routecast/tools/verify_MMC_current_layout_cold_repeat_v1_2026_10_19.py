"""Verify all fixed repeats, retaining differences instead of replacing cold labels."""
import pathlib,json,hashlib,re
from audit_mmc_v16_native_iteration_work_v1 import parse
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_current_layout_cold_repeat_v1_2026-10-19';pp=O/'protocol.json';rp=O/'results.json';p=json.loads(pp.read_text());r=json.loads(rp.read_text());assert r['status']=='ALL3_FIXED_CURRENT_LAYOUT_REPETITIONS_TERMINAL' and r['bindings']==p['bindings'] and p['replications_per_layout']==1 and p['parallel_workers']==2
 for f,h in p['bindings'].items():assert sha(pathlib.Path(f))==h
 rows=[];bindings={str(x):sha(x) for x in [pp,rp,pathlib.Path(__file__).resolve(),R/'tools/audit_mmc_v16_native_iteration_work_v1.py']};fields=['iteration','present_factor_text','BB_updates','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes']
 for plan in p['cases']:
  case=plan['case'];B=pathlib.Path(plan['reference']);D=O/case;recp=D/'receipt.json';rec=json.loads(recp.read_text());assert rec==next(x for x in r['cases'] if x['case']==case)
  for f,h in rec['files'].items():assert sha(pathlib.Path(f))==h
  for name in ['design.blif','design.net','design.place']:assert (B/name).read_bytes()==(D/name).read_bytes()
  assert json.loads((D/'live_process.json').read_text())['command']==plan['command'];assert plan['environment_set']=={'ROUTECAST_NATIVE_OWNER_TRACE':str(D/'owner_trace.tsv')}
  route_equal=(D/'output.route').exists() and (D/'output.route').read_bytes()==(B/'output.route').read_bytes();owner_equal=(D/'owner_trace.tsv').exists() and sha(D/'owner_trace.tsv')==sha(B/'owner_trace.tsv');post_equal=(D/'design.net.post_routing').exists() and (D/'design.net.post_routing').read_bytes()==(B/'design.net.post_routing').read_bytes();assert route_equal==rec['route_bytes_equal'] and owner_equal==rec['owner_trace_bytes_equal'];work_equal=False;qor_equal=False;error=None
  if rec['exit_status']==0:
   try:
    a,b=[parse(x.read_text()) for x in [B/'native.log',D/'native.log']];work_equal=a['iterations']==b['iterations'] and [{k:x[k] for k in fields} for x in a['rows']]==[{k:x[k] for k in fields} for x in b['rows']]
    def qos(text):return (re.findall(r'Total wirelength:\s*(\d+)',text)[-1],re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1])
    qor_equal=qos((B/'native.log').read_text())==qos((D/'native.log').read_text())
   except Exception as e:error=repr(e)
  accepted=rec['exit_status']==0 and rec['FULL_pass'] and rec['vpr_success'] and route_equal and owner_equal and post_equal and work_equal and qor_equal
  row=dict(case=case,exit_zero=rec['exit_status']==0,FULL_pass=rec['FULL_pass'],all_staged_inputs_and_binary_command_identical=True,only_owner_log_destination_relocated=True,route_bytes_equal=route_equal,owner_trace_bytes_equal=owner_equal,postroute_packed_bytes_equal=post_equal,all_integer_work_and_present_factors_equal=work_equal,wirelength_CPD_equal=qor_equal,existing_same_content_physical_and_canonical_proof_transfers=accepted,parse_error=error,repeat_native_seconds=rec['native_seconds']);rows.append(row)
  vp=B.parent/'verification.json';v=json.loads(vp.read_text());assert v['all_native_physical_and_canonical_pass'];assert v['bindings'][str(B/'output.route')]==sha(B/'output.route');assert v['bindings'][str(B/'design.net.post_routing')]==sha(B/'design.net.post_routing')
  for x in [recp,D/'live_process.json',vp,B/'design.net.post_routing']:bindings[str(x)]=sha(x)
  bindings.update(rec['files']);print('CURRENT_REPEAT_VERIFIED',json.dumps(row),flush=True)
 assert [x['case'] for x in rows]==['episode_01','episode_02','episode_03'];all_same=all(x['existing_same_content_physical_and_canonical_proof_transfers'] for x in rows)
 result=dict(status='ALL3_OBSERVED_CURRENT_LAYOUT_REPEAT_ROUTES_OWNERS_AND_INTEGER_WORK_IDENTICAL' if all_same else 'ALL3_FIXED_REPEATS_COMPLETE_DIFFERENCES_PRESERVED_NOT_ADMITTED',cases=rows,bindings=bindings,all3_observed_same_route_owner_trace_and_integer_work=all_same,original_prediction_quality_gate_changed=False,scope='One fixed repeat per current layout, same exact binary/command/input bytes, observation output path private. Positive agreement is only observed repeatability; no universal determinism, causal placement attribution, revised original labels, timing gain or unseen-family claim. Any mismatch remains explicit and requires separate analysis.')
 (O/'independent_verification_v1.json').open('x').write(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
