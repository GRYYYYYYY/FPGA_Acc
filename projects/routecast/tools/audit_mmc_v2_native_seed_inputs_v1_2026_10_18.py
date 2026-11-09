"""Admit all12V2pilot seeds before any native utility execution."""
import json,sys,subprocess,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_v2_native_seed_inputs_v1_2026-10-18';gp=D/'generation_complete.json';generation=json.loads(gp.read_text());assert generation['all9_model_and3trim_seeds_generated'];P=json.loads((D/'protocol.json').read_text());O=D/'independent_audit_logs';O.mkdir();bindings={**generation['bindings'],**closure([Path(__file__)]),str(gp):sha(gp),str(D/'protocol.json'):sha(D/'protocol.json'),str(D/'native_settings_bindings_v1.json'):sha(D/'native_settings_bindings_v1.json')};rows=[]
def run_case(case):
 results=[]
 for mode in ['raw_off','retained_off','retained_on','trim']:
  W=D/case/mode;script=R/'tools'/('verify_mmc_v2_native_trim_seed_v1_2026_10_18.py' if mode=='trim' else 'verify_mmc_v2_native_model_seed_v1_2026_10_18.py');args=[str(R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case),str(W)] if mode=='trim' else [str(W),case,mode];tick=time.perf_counter()
  with (O/(case+'_'+mode+'.log')).open('x') as f:code=subprocess.call([sys.executable,str(script),*args],cwd=R,stdout=f,stderr=subprocess.STDOUT)
  result=dict(case=case,mode=mode,exit_code=code,seconds=time.perf_counter()-tick);results.append(result)
  with (O/(case+'_'+mode+'_terminal.json')).open('x') as f:json.dump(result,f)
  print('SEED AUDIT TERMINAL',result,flush=True)
  if code:break
 return results
with ThreadPoolExecutor(max_workers=3) as pool:
 for future in as_completed([pool.submit(run_case,c) for c in P['case_order']]):rows.extend(future.result());(O/'stages.json').write_text(json.dumps(rows,indent=2))
assert len(rows)==12 and all(x['exit_code']==0 for x in rows)
for row in rows:
 W=D/row['case']/row['mode'];proof=W/'independent_verification_v1.json';v=json.loads(proof.read_text());receipt=W/'receipt.json';r=json.loads(receipt.read_text());assert r['selected_connections']+r['pending_connections']==115572
 if row['mode']=='trim':assert v['complete_disjoint_selected_pending_partition'] and v['all_current_native_local_pins_and_endpoints_match'] and v['uniqueNET_occupancy_monotone_subset_of_authenticated_old_legal_state']
 else:assert v['all_seed_selections_complete_partitions_XML_paths_capacity_and_current_pin_bindings_pass']
 bindings.update(v['bindings']);bindings.update(r['bindings']);bindings[str(proof)]=sha(proof);bindings[str(receipt)]=sha(receipt);bindings[str(W/'seed.route')]=sha(W/'seed.route');row.update(selected_connections=r['selected_connections'],pending_connections=r['pending_connections'])
assert all(sha(p)==h for p,h in bindings.items())
with (D/'seed_admission_verification_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all12_seeds_independently_admitted=True,complete_physical_connection_domain=115572,scope='All3case capacity/current-pin/selector/selected+pending proofs. Partial seeds only; every pending query remains native work, no target route acceptance, QoR or timing gain yet.'),f,indent=2)
print('ALL12V2SEEDS INDEPENDENTLY ADMITTED',flush=True)
