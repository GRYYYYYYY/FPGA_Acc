"""Version observer-only recovery after archived cold equivalence and replay."""
import pathlib,json,hashlib,copy
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def main():
 old=R/'experiments/mmc_prospective_pressure_protocol_v1_2026-10-19';new=R/'experiments/mmc_prospective_pressure_protocol_v2_2026-10-19';eq=R/'experiments/mmc_cold_observer_equivalence_v1_2026-10-19/independent_trace_verification_v1.json'
 if not eq.exists():raise SystemExit('NOT_READY: independent cold observer replay required')
 e=json.loads(eq.read_text());assert e['status']=='ARCHIVED_COLD_OBSERVER_EQUIVALENCE_AND_TRACE_REPLAY_PASS'
 for p,h in e['bindings'].items():assert sha(p)==h,p
 p=old/'protocol.json';original=json.loads(p.read_text());spec=copy.deepcopy(original);bp=R/'build/native_owner_trace_cold_v1_2026-10-19/receipt.json';b=json.loads(bp.read_text());binary=bp.parent/'sequence_vpr';assert sha(binary)==b['binary_sha256'];failure=R/'experiments/mmc_prospective_pressure_native_v1_2026-10-19/observer_scope_failure_review_v1.json';f=json.loads(failure.read_text());assert not f['target_trace_created'] and not f['episode_02_started'] and not f['episode_03_started'];assert not (R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19').exists()
 for job in spec['native_commands']:
  job['argv'][0]=str(binary);job['cwd']=job['cwd'].replace('pressure_native_v1_','pressure_native_v2_');job['environment_set']={k:v.replace('pressure_native_v1_','pressure_native_v2_') for k,v in job['environment_set'].items()}
 for key in original:
  if key not in ['bindings','native_commands']:assert spec[key]==original[key]
 for a,z in zip(original['native_commands'],spec['native_commands']):assert a['argv'][1:]==z['argv'][1:] and a['input_directory']==z['input_directory']
 spec['bindings'].update({str(q):sha(q) for q in [p,eq,bp,binary,failure,pathlib.Path(__file__).resolve()]});spec['recovery_scope']='Observer-only compatibility correction; no prior target iteration/route labels generated. Same predictions, layouts, native options, metrics and gates. Failed v1 retained. Archived cold output bytes and all integer work match; independent trace replay passed.'
 new.mkdir();write(new/'protocol.json',spec)
 add=json.loads((old/'constant_control_addendum_v1.json').read_text());add['parent_protocol_sha256']=sha(new/'protocol.json');add['supersedes_path']=str(old/'constant_control_addendum_v1.json');write(new/'constant_control_addendum_v1.json',add)
 names=['evaluate_MMC_prospective_pressure_v2_2026_10_19.py','prospective_pressure_metrics_v1.py','extract_MMC_prospective_pressure_targets_v2_2026_10_19.py','prospective_pressure_temporal_split_v1.py','verify_MMC_prospective_pressure_traces_v2_2026_10_19.py']
 write(new/'evaluation_code_freeze_v1.json',dict(status='versioned_observer_recovery_consumers_frozen_before_new_native_outcomes',bindings={str(R/'tools'/n):sha(R/'tools'/n) for n in names},native_directory_absent=True,real_runtime_validation_pending=True))
 print('FROZEN RETRY: identical predictions/layouts/options/metrics; cold observer certified',flush=True)
if __name__=='__main__':main()
