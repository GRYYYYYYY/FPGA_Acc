"""Validate frozen4-layout repeat control; never substitute its labels or times."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from audit_mmc_v16_native_iteration_work_v1 import parse

def main():
 E=R/'experiments';root=E/'mmc_same_binary_cold_repeat_v1_2026-10-18';rp=root/'results.json';r=json.loads(rp.read_text());p=json.loads((root/'protocol.json').read_text());assert r['bindings']==p['bindings'];assert all(sha(k)==h for k,h in p['bindings'].items());bindings={**p['bindings'],**closure([Path(__file__)]),str(rp):sha(rp),str(root/'protocol.json'):sha(root/'protocol.json')};assert p['replications_per_layout']==1 and len(p['cases'])==len(r['cases'])==4;rows=[]
 for plan in p['cases']:
  tag=plan['layout'];folder=root/tag;old=Path(plan['reference_directory']);receiptpath=folder/'receipt.json';rec=json.loads(receiptpath.read_text());bindings[str(receiptpath)]=sha(receiptpath);assert rec==next(x for x in r['cases'] if x['layout']==tag);assert all(sha(k)==h for k,h in rec['files'].items());bindings.update(rec['files']);live=json.loads((folder/'live_process.json').read_text());assert live['command']==plan['command'];bindings[str(folder/'live_process.json')]=sha(folder/'live_process.json')
  for name in ['design.blif','design.net','design.place']:
   assert sha(folder/name)==sha(old/name)==p['bindings'][str(old/name)]
  oldroute=old/'output.route';assert sha(oldroute)==plan['reference_route_sha256']==p['bindings'][str(oldroute)];newroute=folder/'output.route';same=rec['exit_status']==0 and newroute.exists() and newroute.read_bytes()==oldroute.read_bytes();assert same==rec['route_bytes_equal'];workequal=False;newwork=None;oldwork=None
  if rec['exit_status']==0:
   oldlog=old/'native.log';newlog=folder/'native.log';oldwork=parse(oldlog.read_text());newwork=parse(newlog.read_text());bindings[str(oldlog)]=sha(oldlog)
   fields=['iteration','present_factor_text','BB_updates','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes'];workequal=oldwork['iterations']==newwork['iterations'] and all({k:a[k] for k in fields}=={k:b[k] for k in fields} for a,b in zip(oldwork['rows'],newwork['rows']))
  if tag=='source':
   vp=old/'verification.json';v=json.loads(vp.read_text());assert v['original_native_FULL_check_pass'] and v['canonical_reload_pass'] and v['overflow_units']==0;bindings[str(vp)]=sha(vp)
  else:
   vp=old.parent/'verification.json';v=json.loads(vp.read_text());assert v['all_native_physical_and_canonical_pass'] and v['bindings'][str(oldroute)]==sha(oldroute);bindings[str(vp)]=sha(vp)
  rows.append(dict(layout=tag,exit_zero=rec['exit_status']==0,one_actual_replication_recorded=True,command_and_all_staged_inputs_equal_reference=True,route_bytes_equal=same,all_integer_iteration_work_and_present_factors_equal=workequal,physical_canonical_proof_transferred_by_exact_inputs_and_route=same,repeat_native_seconds=rec['native_seconds'],iterations=newwork['iterations'] if newwork else None,total_heap_pushes=newwork['total_heap_pushes'] if newwork else None))
 allsame=all(x['route_bytes_equal'] and x['all_integer_iteration_work_and_present_factors_equal'] for x in rows);assert r['all4_route_bytes_equal']==all(x['route_bytes_equal'] for x in rows);assert all(sha(k)==h for k,h in bindings.items())
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all4_observed_same_binary_repeats_route_bytes_and_integer_work_equal' if allsame else 'fixed_repetitions_complete_differences_preserved_require_analysis',bindings=bindings,cases=rows,all4_same_route_and_work=allsame,scope='One fixed replication per layout, baseline-only. Matching route/input content transfers existing physical/canonical admission; no new-route optimality, zero-counter gate repair, universal determinism, causal placement proof or accepted performance gain. Original target labels and every earlier failed quality gate remain unchanged.'),f,indent=2)
 print('REPEAT_VERIFIED',allsame,json.dumps(rows),flush=True)
if __name__=='__main__':main()
