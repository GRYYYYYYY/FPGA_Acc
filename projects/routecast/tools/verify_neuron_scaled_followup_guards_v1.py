"""Queue dependency/resource guards on fixtures; never submit a process."""
import json,os,tempfile
from pathlib import Path
from run_neuron_scaled_present_followup_v1 import predecessor_gate,check,memory_admission,PHYSICAL,STAGES,R
from source_binding_v2 import closure
from pre_route_endpoints import sha


def main():
    checks=0
    def write(path,v):path.write_text(json.dumps(v))
    with tempfile.TemporaryDirectory() as d:
        root=Path(d);folder=root/'case';folder.mkdir();(folder/'model').mkdir()
        assert predecessor_gate(folder,1,'live')['status']=='waiting';checks+=1
        assert predecessor_gate(folder,1,'gone')['status']=='unresolved';checks+=1
        for stage in STAGES:
            write(folder/(stage+'_terminal.json'),dict(exit_status=0))
            write(folder/(stage+'_process.json'),dict(pid=2**62,start_stat=Path('/proc/self/stat').read_text()))
        write(folder/'pipeline_terminal.json',dict(exit_status=0,all_stages_completed=True))
        dev=dict(all_stages_completed=True,present_factor=1,full_original_connections=77106);write(folder/'development_admission.json',dev)
        parity=dict(all_complete_frames_byte_equal=True,all_events_and_round_metadata_equal=True,complete_round_event_digests=[dict(round_index=i,event_count=50767) for i in range(2)]);write(folder/'exact_reference_parity.json',parity)
        for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
            write(folder/'model'/name,{PHYSICAL:True,'completed':77106,'events':101534,'present_factor':1,'independent_owner_sets_scaled_polynomial':True})
        assert predecessor_gate(folder,1,'live')['status']=='waiting';checks+=1
        assert predecessor_gate(folder,1,'unknown')['status']=='unresolved';checks+=1
        assert predecessor_gate(folder,1,'gone')['status']=='ready';checks+=1
        write(folder/'model_terminal.json',dict(exit_status=-9));assert predecessor_gate(folder,1,'gone')['status']=='failed';checks+=1;write(folder/'model_terminal.json',dict(exit_status=0))
        saved=(folder/'model/verification.json').read_text();(folder/'model/verification.json').unlink();assert predecessor_gate(folder,1,'gone')['status']=='unresolved';checks+=1;(folder/'model/verification.json').write_text(saved)
        dev['present_factor']=True;write(folder/'development_admission.json',dev);assert predecessor_gate(folder,1,'gone')['status']=='unresolved';checks+=1;dev['present_factor']=1;write(folder/'development_admission.json',dev)
        parity['complete_round_event_digests'][1]['event_count']=1;write(folder/'exact_reference_parity.json',parity);assert predecessor_gate(folder,1,'gone')['status']=='unresolved';checks+=1;parity['complete_round_event_digests'][1]['event_count']=50767;write(folder/'exact_reference_parity.json',parity)
        old=(folder/'model_process.json').read_text();write(folder/'model_process.json',dict(pid=os.getpid(),start_stat=Path('/proc/self/stat').read_text()));assert predecessor_gate(folder,1,'gone')['status']=='waiting';checks+=1;(folder/'model_process.json').write_text(old)
        file=root/'source';file.write_text('old');bindings={str(file):sha(file)};check(bindings);file.write_text('changed')
        try:check(bindings)
        except RuntimeError:checks+=1
        else:raise AssertionError('source drift allowed')
        for current,expected in [(52*2**30,True),(52*2**30+1,False)]:assert memory_admission(20*2**30,current,80*2**30)['admitted']==expected;checks+=1
    out=R/'experiments/neuron_scaled_followup_guard_contract_v1_2026-10-15';out.mkdir();(out/'verification.json').write_text(json.dumps(dict(bindings=closure([Path(__file__)]),all_pass=True,dependency_and_resource_cases=checks,any_process_submitted=False,scope='Queue cannot submit before complete predecessor markers, full audit/phase counts and process exits; malformed boolean factor, failure, source drift and exact memory boundary covered. Fixture gates only, not scientific model correctness.'),indent=2)+'\n');print(json.dumps(dict(all_pass=True,cases=checks,submitted=False)))


if __name__=='__main__':main()
