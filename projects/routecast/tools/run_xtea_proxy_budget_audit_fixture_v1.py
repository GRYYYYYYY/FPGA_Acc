"""Small complete XTEA producer/auditor fixture for the continue-after-rejection variant."""
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from observe_neuron_scaled_present_pipeline_v1 import process


def main():
    out=R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17'
    old=R/'experiments/xtea_scaled_present_factor1_pipeline_v1_2026-10-15'
    driver=R/'tools/run_design_scoped_quotient_astar_proxy_budget_v1.py'
    physical=R/'tools/verify_proxy_budget_demand_frame_v1.py'
    events=R/'tools/verify_proxy_budget_full_schedule_v1.py'
    endpoint=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json'
    base=R/'experiments/xtea_node_base_wide_v1_2026-10-13/verification.json'
    criticality=R/'experiments/xtea_retained_native_inputs_v1_2026-10-13/criticality'
    contract=R/'experiments/continue_primary_interface_contract_v1_2026-10-17/verification.json'
    proof=json.loads(contract.read_text());assert proof['all_pass']
    assert all(sha(p)==h for p,h in proof['bindings'].items())
    assert json.loads((old/'pipeline_terminal.json').read_text())['all_stages_completed']
    bindings=closure([Path(__file__),driver,physical,events])
    for p in [contract,endpoint,base,criticality/'verification.json',old/'model/initial.json',old/'model/floors.json']:
        bindings[str(p)]=sha(p)
    assert all(sha(p)==h for p,h in bindings.items())
    out.mkdir()
    (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,present_factor=1,
        connections=2450,nets=1448,rounds=2,group_pitch=4,target_cache_entries=512,
        graph_and_initial_paths_floors_and_criticalities_unchanged=True,only_budget_allowance_changed=True,
        search_change='Compiled256-bit exact A* with immutable quotient lower bounds. Heap(f,g,node) can change equal-score paths; no all-state old parity claim.',
        retained_primary_policy="unchanged_fanout16_clean_branches",independent_physical_budget_oracle=True,transaction_auditor_requires_full_coverage_and_isolated_rejected_witnesses=True,
        new_native_labels_used=False,heldout=False,promoted=False,
        scope='Complete exposed-XTEA software producer/auditor fixture only. No neuron causal/quality experiment or new metrics. All original2450connections/two1448NETrounds/3audits; closed neuron A* controls and frozen factor studies untouched.'),indent=2)+'\n')
    m=out/'model'
    stages=[('model',[str(driver),str(endpoint),str(m),str(base),str(criticality),'1']),
            ('initial_audit',[str(physical),str(m),'initial',str(m/'initial_physical_verification.json')]),
            ('sketch_audit',[str(physical),str(m),'sketch',str(m/'sketch_physical_verification.json')]),
            ('event_audit',[str(events),str(m),'xtea',str(m/'verification.json'),'1'])]
    for name,args in stages:
        metadata=json.loads((R/'experiments/neuron_quotient_astar_pipeline_v1_2026-10-17/model_process.json').read_text())
        live=process(metadata['pid'],int(metadata['start_stat'].rsplit(')',1)[1].split()[19]),metadata['args'])
        reserve=max(0,20*2**30-live['memory_KiB']['VmSize']*1024) if live.get('verified_live') else 20*2**30
        limit=2**30
        free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
        admission=dict(shared_headroom_bytes=free,remaining_factor4_reservation_bytes=reserve,
                       child_limit_bytes=limit,margin_bytes=8*2**30,admitted=free>=reserve+limit+8*2**30)
        with (out/(name+'_admission.json')).open('x') as stream:json.dump(admission,stream)
        assert admission['admitted'],'Full candidate stage not admitted; no retry'
        assert all(sha(p)==h for p,h in bindings.items())
        tick=time.perf_counter()
        with (out/(name+'.log')).open('x') as log:
            child=subprocess.Popen([sys.executable,*args],cwd=R,stdout=log,stderr=subprocess.STDOUT,
                preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_AS,(limit,limit)))
            (out/(name+'_process.json')).write_text(json.dumps(dict(pid=child.pid,args=child.args,
                start_stat=Path(f'/proc/{child.pid}/stat').read_text(),address_space_limit_bytes=limit))+'\n')
            print('PROXY BUDGET XML FIXTURE START',name,child.pid,flush=True)
            code=child.wait()
        (out/(name+'_terminal.json')).write_text(json.dumps(dict(exit_status=code,seconds=time.perf_counter()-tick,address_space_limit_bytes=limit))+'\n')
        if code:raise SystemExit(code)
    assert all(sha(p)==h for p,h in bindings.items())
    assert sha(m/'floors.json')==sha(old/'model/floors.json')
    def initial_without_budget(path):
        value=json.loads(path.read_text())
        for rec in value['records']:rec.pop('budget_integer')
        return value
    assert initial_without_budget(m/'initial.json')==initial_without_budget(old/'model/initial.json')
    proof=json.loads((m/'verification.json').read_text())
    assert proof['completed']==2450 and proof['events']==2896 and proof['present_factor']==1
    assert proof['independent_owner_sets_scaled_polynomial'] is True
    assert proof['complete_primary_search_after_rejection_and_isolated_witnesses_pass'] is True
    assert all(sha(p)==h for p,h in proof['bindings'].items())
    (out/'pipeline_terminal.json').write_text(json.dumps(dict(exit_status=0,all_stages_completed=True,
        all_original_connections=2450,full_NET_events=2896,initial_paths_and_ledgers_identical_floors_byte_identical=True,
        final_overflow=proof['overflow_units'],promoted=False))+'\n')
    print('PASS complete proxy-budget XTEA XML fixture and all3 independent audits',proof['overflow_units'],flush=True)


if __name__=='__main__':main()
