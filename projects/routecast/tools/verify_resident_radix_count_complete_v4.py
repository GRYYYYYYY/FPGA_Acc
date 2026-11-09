"""Independent complete count-candidate cohort admission; never a speed proof."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/resident_radix_count_complete_v4_2026-10-08'
def load(p):return json.loads(p.read_text())
def auth(d):
 for section in ['bindings','files']:
  for p,h in d.get(section,{}).items():assert sha(p)==h,p
r=load(D/'receipt.json');protocol=load(D/'protocol.json');auth(r);auth(protocol)
assert r['bindings']==protocol['bindings']
assert [x['name'] for x in r['rows']]==['xtea','8051','mmc']
expected=dict(xtea=(2450,2555,2555,0),**{'8051':(16503,14720,14719,1)},mmc=(115572,98479,98334,145))
bindings={**r['bindings'],str(D/'receipt.json'):sha(D/'receipt.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(Path(__file__))};rows=[]
for row in r['rows']:
 name=row['name'];out=D/name;assert row['status']=='COMPLETE_CORRECTNESS_VERIFIED'
 assert set(row['proofs'])=={str(out/f) for f in ['parity_verification.json','initial_physical_verification.json','sketch_physical_verification.json','verification.json']}
 for p,h in row['proofs'].items():assert sha(p)==h;auth(load(Path(p)));bindings[p]=h
 parity=load(out/'parity_verification.json')
 assert parity['all_five_complete_state_files_byte_equal'] and parity['all_feedback_events_price_schedule_epoch_and_outcome_equal']
 count,events,commit,retain=expected[name]
 for frame in ['initial','sketch']:
  p=load(out/(frame+'_physical_verification.json'))
  assert p['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and p['completed']==count
 replay=load(out/'verification.json')
 assert replay['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
 assert replay['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
 assert (replay['completed'],replay['events'],replay['committed'],replay['retained'])==(count,events,commit,retain)
 receipt=load(out/'receipt.json');auth(receipt);bindings[str(out/'receipt.json')]=sha(out/'receipt.json')
 rows.append(dict(name=name,completed=count,events=events,committed=commit,retained=retain,complete_state_event_and_independent_physical_audits_pass=True))
assert all(sha(p)==h for p,h in bindings.items())
(D/'independent_verification_v4.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_three_complete_case_correctness_gates_pass=True,scope='Known-case count-update candidate correctness only. No paired runtime, complete workflow, unseen-family, original HDL, physical timing or silicon proof.'),indent=2)+'\n')
print(json.dumps(rows,indent=2))
