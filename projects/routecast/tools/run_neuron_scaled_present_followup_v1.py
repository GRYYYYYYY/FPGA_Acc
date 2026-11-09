"""Single owner for future factors2/4; existing factor1 is observed only.

Never recovers a failed/ambiguous attempt. HOLD prevents the next submission;
no running model, original supervisor or other project process is signalled.
"""
import argparse,datetime,json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from run_neuron_scaled_present_pipeline_v1 import memory_admission
O=R/'experiments/neuron_scaled_present_followup_v1_2026-10-15'
DRIVER=R/'tools/run_neuron_scaled_present_pipeline_v1.py'
NUMERIC=R/'experiments/neuron_scaled_present_integer_bounds_v1_2026-10-15/verification.json'
GUARD=R/'experiments/neuron_scaled_followup_guard_contract_v1_2026-10-15/verification.json'
PHYSICAL='all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'
STAGES=('model','initial_audit','sketch_audit','event_audit')


def case(factor):return R/f'experiments/titan23_neuron_scaled_present_factor{factor}_pipeline_v1_2026-10-15'


def read(path):
    with Path(path).open('rb') as f:data=f.read(2**20+1)
    if len(data)>2**20:raise ValueError('metadata above1MiB bound')
    value=json.loads(data)
    if type(value) is not dict:raise ValueError('metadata is not object')
    return value


def success(v):return type(v.get('exit_status')) is int and v['exit_status']==0


def owner_state(pid,startticks):
    try:
        a=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
        return 'gone' if int(a[19])!=startticks or a[0] in ('Z','X') else 'live'
    except FileNotFoundError:return 'gone'
    except (PermissionError,ValueError,IndexError):return 'unknown'


def predecessor_gate(folder,factor,owner):
    missing=[]
    try:
        for stage in STAGES:
            p=folder/(stage+'_terminal.json')
            if not p.exists():missing.append(p.name);continue
            if not success(read(p)):return dict(status='failed',reason=stage+' nonzero/invalid terminal')
        names=['pipeline_terminal.json','development_admission.json']+(['exact_reference_parity.json'] if factor==1 else [])
        missing.extend(n for n in names if not (folder/n).exists())
        if missing:return dict(status='waiting' if owner=='live' else 'unresolved',missing=missing,owner=owner)
        pipeline=read(folder/'pipeline_terminal.json');dev=read(folder/'development_admission.json')
        if not success(pipeline) or pipeline.get('all_stages_completed') is not True or dev.get('all_stages_completed') is not True or type(dev.get('present_factor')) is not int or dev.get('present_factor')!=factor or dev.get('full_original_connections')!=77106:
            return dict(status='unresolved',reason='invalid complete pipeline/development evidence')
        if factor==1:
            parity=read(folder/'exact_reference_parity.json')
            if parity.get('all_complete_frames_byte_equal') is not True or parity.get('all_events_and_round_metadata_equal') is not True:return dict(status='unresolved',reason='factor1 complete parity not admitted')
            digests=parity.get('complete_round_event_digests',[])
            if len(digests)!=2 or any(x.get('round_index')!=i or x.get('event_count')!=50767 for i,x in enumerate(digests)):return dict(status='unresolved',reason='factor1 full event counts missing')
        for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
            proof=read(folder/'model'/name)
            if proof.get(PHYSICAL) is not True or proof.get('completed')!=77106:return dict(status='unresolved',reason='incomplete independent audit')
            if name=='verification.json' and (proof.get('events')!=101534 or proof.get('present_factor')!=factor or proof.get('independent_owner_sets_scaled_polynomial') is not True):return dict(status='unresolved',reason='incomplete full scaled transaction proof')
        if owner!='gone':return dict(status='waiting' if owner=='live' else 'unresolved',reason='previous supervisor not confirmed gone',owner=owner)
        for stage in STAGES:
            m=read(folder/(stage+'_process.json'));start=int(m['start_stat'].rsplit(')',1)[1].split()[19])
            if owner_state(m['pid'],start)!='gone':return dict(status='waiting',reason='previous stage process not gone',stage=stage)
        return dict(status='ready',previous_factor=factor)
    except (OSError,ValueError,KeyError,IndexError,TypeError) as error:return dict(status='unresolved',reason=type(error).__name__+': '+str(error))


def check(bindings):
    for p,h in bindings.items():
        if sha(p)!=h:raise RuntimeError('Frozen followup source/input changed: '+p)


def status(value):
    value=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**value)
    tmp=O/'status.tmp';tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(O/'status.json')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');args=parser.parse_args()
    launch=read(case(1)/'launch_observation_v1.json');prior_owner=(launch['supervisor_pid'],launch['supervisor_startticks'])
    gate=predecessor_gate(case(1),1,owner_state(*prior_owner))
    if not args.run:print(json.dumps(gate,indent=2));return
    g=read(GUARD);assert g['all_pass'];check(g['bindings'])
    n=read(NUMERIC)
    assert n['all_pass'] and n['complete_graph_nodes']==3593250 and n['complete_connections']==77106
    assert {x['factor'] for x in n['rows']}=={1,2,4}
    assert all(x['price_store128_admitted'] and x['native_raw128_admitted'] and x['native_weighted240_admitted'] for x in n['rows'])
    bindings=closure([Path(__file__),DRIVER])
    for p in [NUMERIC,GUARD,case(1)/'launch_observation_v1.json',R/'experiments/neuron_scaled_present_ablation_prereg_v1_2026-10-15/protocol.json']:
        bindings[str(p)]=sha(p)
    check(bindings)
    # Atomic creation is the one-attempt ownership claim. Never adopt/restart
    # an existing output directory on a second invocation of this queue.
    O.mkdir()
    (O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,planned_factors=[2,4],existing_factor1_directory=str(case(1)),source_and_integer_gates_frozen=True,policy='Observe factor1 only; require all predecessor stages, complete factor1 parity, all child/supervisor exits, then fresh20GiB+8GiB admission. Only invoke the existing full runner once per future factor. No recovery or retry after a child failure; do not select factors by quality.',scope='Deterministic future development queue, not model/quality/whole-goal completion.'),indent=2)+'\n')
    (O/'process.json').write_text(json.dumps(dict(pid=os.getpid(),start_stat=Path('/proc/self/stat').read_text(),args=sys.argv))+'\n')
    submitted=[]
    try:
        for factor in (2,4):
            previous=1 if factor==2 else 2
            while True:
                check(bindings)
                if (O/'HOLD').exists():
                    status(dict(phase='held_before_new_submission',submitted_factors=submitted,next_factor=factor));return
                gate=predecessor_gate(case(previous),previous,owner_state(*prior_owner))
                if gate['status'] in ('failed','unresolved'):raise RuntimeError('Predecessor refused: '+json.dumps(gate))
                if gate['status']=='ready':
                    if case(factor).exists():raise RuntimeError('Future output already exists; refuse duplicate/adoption: '+str(case(factor)))
                    admission=memory_admission(20*2**30,int(Path('/sys/fs/cgroup/memory.current').read_text()),int(Path('/sys/fs/cgroup/memory.max').read_text()))
                    status(dict(phase='ready' if admission['admitted'] else 'waiting_for_memory',next_factor=factor,submitted_factors=submitted,predecessor=gate,admission=admission))
                    if admission['admitted']:break
                else:status(dict(phase='waiting_for_predecessor',next_factor=factor,submitted_factors=submitted,predecessor=gate))
                time.sleep(30)
            with (O/f'factor{factor}_controller.log').open('x') as log:
                child=subprocess.Popen([sys.executable,str(DRIVER),str(factor),'--run'],cwd=R,stdout=log,stderr=subprocess.STDOUT)
                m=dict(pid=child.pid,start_stat=Path(f'/proc/{child.pid}/stat').read_text(),args=child.args)
                (O/f'factor{factor}_controller_process.json').write_text(json.dumps(m)+'\n')
                prior_owner=(child.pid,int(m['start_stat'].rsplit(')',1)[1].split()[19]));submitted.append(factor)
                print('FOLLOWUP START factor',factor,'controller',child.pid,flush=True)
                while child.poll() is None:
                    status(dict(phase='controller_running',current_factor=factor,submitted_factors=submitted,controller_pid=child.pid));time.sleep(30)
            (O/f'factor{factor}_controller_terminal.json').write_text(json.dumps(dict(exit_status=child.returncode))+'\n')
            if child.returncode:raise RuntimeError('Child controller failed; no retry, no next factor')
            gate=predecessor_gate(case(factor),factor,'gone')
            if gate['status']!='ready':raise RuntimeError('Completed controller lacks required complete evidence: '+json.dumps(gate))
        check(bindings);status(dict(phase='all_followup_factors_complete',submitted_factors=submitted))
        (O/'terminal.json').write_text(json.dumps(dict(exit_status=0,all_planned_followup_factors_completed=True,goal_complete=False))+'\n')
    except BaseException as error:
        status(dict(phase='stopped_requires_analysis',submitted_factors=submitted,error=type(error).__name__+': '+str(error)))
        (O/'terminal.json').write_text(json.dumps(dict(exit_status=1,all_planned_followup_factors_completed=False,error=str(error)))+'\n');raise


if __name__=='__main__':main()
