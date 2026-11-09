"""Serialize fixed candidate seed records and run unchanged independent audits."""
import json,sys,subprocess,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from shared_compact_native_inventory_v1 import Inventory
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
from versioned_digest_cache_v1 import Cache

def main():
 preflight=R/'experiments/mmc_terminal_native_seed_preflight_v1_2026-10-18';pp=preflight/'receipt.json';p=json.loads(pp.read_text());assert p['status']=='all3_native_seed_record_boundary_preflight_pass'
 admission=R/'experiments/mmc_terminal_commit_replay_v1_2026-10-18/verification.json';a=json.loads(admission.read_text());assert a['status']=='pass'
 original=R/'experiments/mmc_v2_native_seed_inputs_v1_2026-10-18/protocol.json';old=json.loads(original.read_text())
 verifier=R/'tools/verify_mmc_v2_native_model_seed_v1_2026_10_18.py'
 bindings={**p['bindings'],**a['bindings'],**old['bindings'],str(pp):sha(pp),str(admission):sha(admission),str(original):sha(original),**closure([Path(__file__),verifier])}
 d=R/'experiments/mmc_terminal_native_seed_inputs_v1_2026-10-18';d.mkdir();(d/'logs').mkdir()
 cases=['case_01','case_02','case_03'];frames={case:{'candidate':str(R/'experiments/mmc_terminal_batch_commit_v2_2026-10-18'/case/'frame.json')} for case in cases}
 with (d/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,case_order=cases,frames=frames,frame_proofs={case:{'candidate':str(admission)} for case in cases},native_settings=old['native_settings'],primary_candidate='candidate',controls=['retained_off','retained_on','raw_off','trim','cold'],archived_native_control_root=str(R/'experiments/mmc_v2_native_utility_v1_2026-10-18'),utility_screen='All3 cases required: candidate must strictly reduce exact heap pushes versus each frozen control and not worsen wirelength or diagnosticCPD versus any control. All arms must pass FULL native, full physical/canonical audits;330ignored fixups remain explicit. No arm/case replacement or forecast gate changes.',scope='Fixed development-only native utility pilot, independent of failed forecast branch. No native launch until all3 new seeds independently admitted. Cached frame/serialization clocks and archived controls are not fresh balanced end-to-end speedup evidence.'),stream,indent=2)
 cache=Cache();rows=[]
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items());inventory=None
  for case in cases:
   epfile=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'demand/endpoints.json';ep=json.loads(epfile.read_text())
   if inventory is None:
    print('LOAD SHARED NATIVE SEED INVENTORY',flush=True);inventory=Inventory(Path(ep['inputs']['graph']['path']))
   inventory.validate(Path(ep['inputs']['graph']['path']),ep['graph_sha256'])
   path=preflight/case/'candidate_subset.json';assert bindings[str(path)]==sha(path);subset=json.loads(path.read_text());tick=time.perf_counter()
   text,pins=serialize_subset(dict(records=subset['records']),epfile,Path(ep['inputs']['native_identity']['path']),Path(ep['inputs']['place']['path']),inventory)
   folder=d/case/'candidate';folder.mkdir(parents=True)
   for name,value in [('seed.route',text),('subset.json',json.dumps(subset)),('pin_bindings.json',json.dumps(pins))]:
    with (folder/name).open('x') as stream:stream.write(value+'\n')
   selected={r['connection_id'] for r in subset['records']};required={q['connection_id'] for q in ep['connections']}
   assert selected.isdisjoint(subset['pending']) and selected|set(subset['pending'])==required and len(required)==115572
   wb={**bindings,str(d/'protocol.json'):sha(d/'protocol.json'),str(epfile):sha(epfile),**{str(folder/name):sha(folder/name) for name in ['seed.route','subset.json','pin_bindings.json']}}
   row=dict(case=case,mode='candidate',selected_connections=len(selected),pending_connections=len(subset['pending']),selected_nets=len({r['net_id'] for r in subset['records']}),preparation_seconds=time.perf_counter()-tick)
   with (folder/'receipt.json').open('x') as stream:json.dump(dict(bindings=wb,**row,complete_partition_and_capacity_pass=True,independent_audit_pending=True,scope='Serialized fixed completeNET candidate subset only; every pending query remains required native work.'),stream,indent=2)
   rows.append(row);print('SERIALIZED CANDIDATE SEED',json.dumps(row),flush=True)
  assert all(sha(path)==h for path,h in bindings.items())
 del inventory
 def audit(case):
  folder=d/case/'candidate'
  with (d/'logs'/(case+'_audit.log')).open('x') as stream:
   code=subprocess.call([sys.executable,str(verifier),str(folder),case,'candidate'],cwd=R,stdout=stream,stderr=subprocess.STDOUT)
  return dict(case=case,exit_code=code)
 stages=[]
 with ThreadPoolExecutor(max_workers=3) as pool:
  for future in as_completed([pool.submit(audit,case) for case in cases]):
   stages.append(future.result());(d/'stages.json').write_text(json.dumps(stages,indent=2));print('SEED AUDIT TERMINAL',stages[-1],flush=True)
 assert len(stages)==3 and all(s['exit_code']==0 for s in stages)
 with cache.installed():
  for case in cases:
   folder=d/case/'candidate';proof=folder/'independent_verification_v1.json';v=json.loads(proof.read_text());assert v['all_seed_selections_complete_partitions_XML_paths_capacity_and_current_pin_bindings_pass']
   bindings.update(v['bindings']);bindings[str(proof)]=sha(proof)
   for name in ['receipt.json','seed.route','subset.json','pin_bindings.json','independent_seed_physical_audit_v1.json']:bindings[str(folder/name)]=sha(folder/name)
  assert all(sha(path)==h for path,h in bindings.items())
  with (d/'seed_admission_verification_v1.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,rows=rows,all3_seeds_independently_admitted=True,scope='Fixed candidate seed selector/path/switch/currentpin/capacity/full selected+pending partition verified. No new native routing executed, no QoR, timing or forecast gain.'),stream,indent=2)
 print('ALL3 TERMINAL CANDIDATE NATIVE SEEDS INDEPENDENTLY ADMITTED',flush=True)

if __name__=='__main__':main()
