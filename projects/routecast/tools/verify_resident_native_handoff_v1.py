"""Authenticate complete handoff model semantics and unchanged whole-NET seed bytes."""
import json, sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
case=sys.argv[1];assert case in ['xtea','mmc']
D=R/f'experiments/{case}_resident_native_handoff_v1_2026-10-09'
old=(R/'experiments/resident_hybrid_complete_v5_2026-10-08/xtea/resident' if case=='xtea'
     else R/'experiments/ultraembedded_mmc_continuous_workflow_v8_2026-10-09/seed/model/mmc')
seed=(R/'experiments/xtea_seed_selection_native_routes_v1_2026-10-09/connection_count' if case=='xtea'
      else R/'experiments/ultraembedded_mmc_continuous_workflow_v8_2026-10-09/seed/native/mmc')
bindings=closure([Path(__file__)])
def checked(path):
    data=json.loads(path.read_text())
    for section in ['bindings','files']:
        assert all(sha(p)==h for p,h in data.get(section,{}).items())
    bindings[str(path)]=sha(path)
    return data
pipeline=checked(D/'receipt.json')
receipts=[]
for directory in [old,D/'model']:
    receipts.append(checked(directory/'receipt.json'))
    for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
        proof=checked(directory/name)
        assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
    assert proof['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
epfiles=[next(Path(p) for p in r['bindings'] if p.endswith('/endpoints.json')) for r in receipts]
assert sha(epfiles[0])==sha(epfiles[1])
for name in ['floors.json','initial.json','sketch.json','round0.json','round1.json']:
    a,b=old/name,D/'model'/name
    assert json.loads(a.read_text())==json.loads(b.read_text()),name
    bindings.update({str(a):sha(a),str(b):sha(b)})
assert len(receipts[0]['rounds'])==len(receipts[1]['rounds'])==2
for a,b in zip(receipts[0]['rounds'],receipts[1]['rounds']):
    assert {k:v for k,v in a.items() if k not in ['state_file','seconds']}=={k:v for k,v in b.items() if k not in ['state_file','seconds']}
seed_receipt=checked(seed.parent/'receipt.json' if case=='xtea' else seed/'receipt.json')
for name in ['seed.route','bindings.json']:
    a,b=seed/name,D/'native'/name
    assert seed_receipt['files'][str(a)]==sha(a)
    assert a.read_bytes()==b.read_bytes(),name
    bindings.update({str(a):sha(a),str(b):sha(b)})
subset=json.loads((D/'native/subset.json').read_text())
baseline=(R/'experiments/xtea_seed_selection_order_v1_2026-10-09/connection_count.json' if case=='xtea' else seed/'subset.json')
data=json.loads(baseline.read_text());bindings[str(baseline)]=sha(baseline)
assert all(subset[k]==data[k] for k in ['records','pending','decisions'])
assert len(subset['records'])==pipeline['selected_connections']
assert len(subset['pending'])==pipeline['pending_connections']
assert pipeline['selected_connections']+pipeline['pending_connections']==pipeline['required_connections']
assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,complete_model_frames_and_events_equal=True,
         complete_seed_bytes_pin_bindings_selection_and_pending_equal=True,
         required=pipeline['required_connections'],selected=pipeline['selected_connections'],pending=pipeline['pending_connections'],
         scope='Authenticated full development-case model/context handoff and unchanged seed serialization; all required pending preserved. No exact native import/canonical run or complete cost gain proof.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print('PASS complete handoff model/events/seed/selection/pending',case)
