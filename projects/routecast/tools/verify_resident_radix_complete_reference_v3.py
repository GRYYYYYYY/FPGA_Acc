"""Authenticate all three complete radix model correctness cohorts; no speed claim."""
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / 'tools'))
from pre_route_endpoints import sha

bindings = {str(Path(__file__)): sha(Path(__file__))}
rows = []
for name, count, events, committed, retained in [
    ('xtea', 2450, 2555, 2555, 0),
    ('8051', 16503, 14720, 14719, 1),
    ('mmc', 115572, 98479, 98334, 145),
]:
    folder = (R / 'experiments/freecores_resident_radix_v3_2026-10-08' / name
              if name != 'mmc' else
              R / 'experiments/ultraembedded_mmc_resident_radix_v3_2026-10-08/mmc')
    for filename in ['parity_verification.json', 'initial_physical_verification.json',
                     'sketch_physical_verification.json', 'events_verification_v4.json']:
        path = folder / filename
        proof = json.loads(path.read_text())
        for source, digest in {str(path): sha(path), **proof['bindings']}.items():
            if source in bindings:
                assert bindings[source] == digest, source
            bindings[source] = digest
        if filename == 'parity_verification.json':
            assert proof['name'] == name
            assert proof['all_five_complete_state_files_byte_equal']
            assert proof['all_feedback_events_price_schedule_epoch_and_outcome_equal']
        else:
            assert proof['completed'] == count
            assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
        if filename == 'events_verification_v4.json':
            assert proof['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
            assert (proof['events'], proof['committed'], proof['retained']) == (events, committed, retained)
    rows.append(dict(name=name, completed=count, events=events,
                     committed=committed, retained=retained, full_reference_pass=True))
assert all(sha(source) == digest for source, digest in bindings.items())
out = R / 'experiments/resident_radix_complete_reference_v3_2026-10-08'
out.mkdir()
(out / 'verification.json').write_text(json.dumps(dict(
    bindings=bindings, rows=rows,
    scope='All original physical queries, five complete state files and all feedback events; independent initial/final XML Fraction RC, budgets, ownership, prices, epochs and ledger rebuild audits. Known-case correctness, no speed, heldout-family, original HDL, native workflow or hardware proof.'
), indent=2) + '\n')
print('PASS radix all three complete correctness cohorts', flush=True)
