"""One read-only complete replay of the closed retained control, no model launch."""
import json
import os
import resource
import sys
from pathlib import Path
import neuron_no_retention_trial_v2 as trial
from source_binding_v2 import closure

OUT=trial.R/'experiments/neuron_transaction_objective_components_v1_2026-10-17'
REPLAY=trial.R/'tools/replay_neuron_objective_components_v1.py'


def main():
    contract=trial.R/'experiments/neuron_objective_component_contract_v1_2026-10-17/verification.json'
    value=trial.load(contract);assert value['all_pass'];trial.check(value['bindings'])
    admission=trial.BASELINE/'independent_final_admission_v1.json'
    assert trial.load(admission)['all_pass']
    assert trial.load(trial.OUT/'metrics/verification.json')['all_pass']
    bindings=closure([Path(__file__),REPLAY])
    for p in (contract,admission,trial.OUT/'research_decision_v1_2026-10-17.json',
              trial.R/'experiments/neuron_retention_hotspot_NET_owners_v1_2026-10-17/verification.json'):
        bindings[str(p)]=trial.sha(p)
    trial.check(bindings)
    OUT.mkdir()
    trial.write(OUT/'protocol.json',dict(bindings=bindings,original_connections=77106,full_NET_events=101534,
        selected_NETs=[56,1768,21348,21505],selection='Previously identified leading error-region contributors, fixed before component replay.',
        components=['criticality_raw','resource_base','history','present','history_present_interaction','static_span'],
        policy='Original independent XML/Fraction full event replay preserved. Capture exact sum decomposition at actual union_objective call before transaction commit, owner exclusion included. All events audited; only selected NET components recorded.',
        no_new_model_or_native_route=True,post_label_development=True,promoted=False))
    trial.write(OUT/'process.json',dict(pid=os.getpid(),start_stat=Path('/proc/self/stat').read_text(),args=Path('/proc/self/cmdline').read_bytes().decode().strip('\0').split('\0')))
    try:
        trial.run_stage(OUT,'retained_replay',[REPLAY,trial.BASELINE/'model','neuron',OUT/'verification.json','1'],8*2**30,3600)
        proof=trial.load(OUT/'verification.json')
        assert proof['events']==101534 and proof['exact_transaction_component_sum_verified']
        assert {row['net_id'] for row in proof['snapshot_objective_components']}=={56,1768,21348,21505}
        trial.check(bindings)
        trial.write(OUT/'terminal.json',dict(exit_status=0,complete_replay_and_exact_component_capture_pass=True,new_model_launched=False))
    except BaseException as error:
        trial.write(OUT/'terminal.json',dict(exit_status=1,error_type=type(error).__name__,error=str(error),no_retry=True))
        raise


if __name__=='__main__':main()
