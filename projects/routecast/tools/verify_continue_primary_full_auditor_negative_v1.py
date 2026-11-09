"""Mutate only a private fixture receipt; original outputs are never changed."""
import json
from pathlib import Path
import neuron_no_retention_trial_v2 as trial


def main():
    src=trial.R/'experiments/xtea_continue_primary_audit_fixture_v1_2026-10-17/model'
    original=trial.sha(src/'receipt.json')
    assert trial.load(src.parent/'pipeline_terminal.json')['all_stages_completed']
    out=trial.R/'experiments/continue_primary_full_auditor_negative_v1_2026-10-17';out.mkdir()
    model=out/'model';model.mkdir()
    for p in src.iterdir():
        if p.name not in ('receipt.json','verification.json'): (model/p.name).symlink_to(p)
    receipt=trial.load(src/'receipt.json');changed=False
    for rr in receipt['rounds']:
        for event in rr['events']:
            for row in event['primary_rejected_expansions']:
                if not changed and row['status']=='RETAIN_RAW_BUDGET':
                    row['raw']+=1;changed=True
    assert changed
    trial.write(model/'receipt.json',receipt)
    auditor=trial.R/'tools/verify_scaled_present_continue_primary_full_schedule_v1.py'
    try:
        trial.run_stage(out,'corrupt_witness',[auditor,model,'xtea',out/'unexpected_success.json','1'],2**30,3600)
    except AssertionError:pass
    else:raise AssertionError('Corrupt raw witness accepted')
    terminal=trial.load(out/'corrupt_witness_terminal.json');assert terminal['exit_status']==1 and terminal['timed_out'] is False
    log=(out/'corrupt_witness.log').read_text()
    assert 'audit_continue_primary_event_v1.py' in log and "actual==row['raw']" in log and 'AssertionError' in log
    assert not (out/'unexpected_success.json').exists() and trial.sha(src/'receipt.json')==original
    trial.write(out/'verification.json',dict(all_pass=True,original_fixture_unchanged=True,
        corrupt_raw_witness_rejected_by_full_original_XML_replay_at_expected_assertion=True,
        no_success_proof_written=True,expected_negative_terminal=terminal,
        bindings={str(p):trial.sha(p) for p in (Path(__file__),auditor,src/'receipt.json',model/'receipt.json',out/'corrupt_witness.log')},
        no_neuron_model_launched=True))
    print('PASS full-auditor corrupted rejection witness refused; original fixture preserved')


if __name__=='__main__':main()
