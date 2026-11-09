"""Authenticate full reference cases before complete MMC radix queue trial."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
bindings={**closure([Path(__file__),R/'tools/run_resident_soft_demand_radix_v3.py'])}
rows=[]
for name,count,events in [('8051',16503,14720),('xtea',2450,2555)]:
 d=R/'experiments/freecores_resident_radix_v3_2026-10-08'/name
 for filename in ['parity_verification.json','initial_physical_verification.json','sketch_physical_verification.json','events_verification_v4.json']:
  p=d/filename;data=json.loads(p.read_text());bindings[str(p)]=sha(p)
  for k,h in data['bindings'].items():
   if k in bindings:assert bindings[k]==h,k
   bindings[k]=h
  if filename=='parity_verification.json':assert data['all_five_complete_state_files_byte_equal'] and data['all_feedback_events_price_schedule_epoch_and_outcome_equal']
  else:assert data['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and data['completed']==count
  if filename=='events_verification_v4.json':assert data['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and data['events']==events
 rows.append(dict(name=name,completed=count,events=events,full_reference_pass=True))
assert all(sha(k)==h for k,h in bindings.items())
out=R/'experiments/resident_radix_reference_v3_2026-10-08';out.mkdir()
(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Full 8051/XTEA five state bytes and all event/initial/final physical gates; no paired speed or MMC generalization.'),indent=2)+'\n')
print('Full two-case reference certification PASS; launch full MMC',flush=True)
endpoint=R/'experiments/ultraembedded_mmc_native_demand_v1_2026-10-08/mmc/endpoints.json'
destination=R/'experiments/ultraembedded_mmc_resident_radix_v3_2026-10-08/mmc'
result=subprocess.run([sys.executable,str(R/'tools/run_resident_soft_demand_radix_v3.py'),str(endpoint),str(destination)],cwd=R,timeout=1800)
assert result.returncode==0,result.returncode
