"""Sequential full neuron ablations, gated on original certified termination.

Never starts, stops or recovers the original experiment. Existing stage starts
without terminal evidence are refused, not retried. Explicit --run is required.
"""
import argparse, gc, json, resource, subprocess, sys, time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from verify_neuron_compiled_final_admission_v1 import event_digest

ORIGINAL=R/'experiments/titan23_neuron_compiled_criticality_pipeline_v1_2026-10-15'
FINAL=R/'experiments/neuron_compiled_final_admission_v1_2026-10-15/verification.json'
SCRIPTS=['run_design_scoped_scaled_present_retained_tree_v1.py','verify_resident_demand_frame_direct_lattice_v7.py','verify_scaled_present_retained_tree_full_schedule_v1.py']
STAGES=('model','initial_audit','sketch_audit','event_audit')
FRAMES=('initial.json','floors.json','round0.json','round1.json','sketch.json')


def read(path):
    with Path(path).open() as f:return json.load(f)


def write(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2);f.write('\n')


def ensure(path,value):
    if Path(path).exists():assert read(path)==value
    else:write(path,value)


def stage_action(terminal, started):
    if terminal is not None:
        return 'done' if type(terminal.get('exit_status')) is int and terminal['exit_status']==0 else 'failed'
    return 'unresolved_started_stage' if started else 'launch'


def memory_admission(limit,current,maximum,margin=8*2**30):
    if any(type(x) is not int or x<0 for x in (limit,current,maximum,margin)) or current>maximum:
        raise ValueError('invalid memory accounting')
    return dict(child_limit_bytes=limit,shared_memory_current_bytes=current,
                shared_memory_max_bytes=maximum,margin_bytes=margin,
                admitted=maximum-current>=limit+margin)


def readiness(factor):
    if type(factor) is not int or factor not in (1,2,4):raise ValueError('factor')
    required=[FINAL,ORIGINAL/'pipeline_terminal.json',ORIGINAL/'exact_reference_parity.json',
        R/'experiments/scaled_present_full_audit_corruption_v1_2026-10-15/verification.json',
        R/'experiments/xtea_scaled_present_full_comparison_v1_2026-10-15/research_decision_v1.json']
    if factor>1:
        required.append(R/'experiments/titan23_neuron_scaled_present_factor1_pipeline_v1_2026-10-15/exact_reference_parity.json')
    if factor==4:
        required.append(R/'experiments/titan23_neuron_scaled_present_factor2_pipeline_v1_2026-10-15/development_admission.json')
    return dict(factor=factor,ready=all(p.is_file() for p in required),missing=[str(p) for p in required if not p.is_file()],required=[str(p) for p in required])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('factor',type=int,choices=[1,2,4]);parser.add_argument('--run',action='store_true');args=parser.parse_args()
    pre=readiness(args.factor);pre['model_memory']=memory_admission(20*2**30,int(Path('/sys/fs/cgroup/memory.current').read_text()),int(Path('/sys/fs/cgroup/memory.max').read_text()))
    if not args.run or not pre['ready']:
        print(json.dumps(pre,indent=2));return
    out=R/f'experiments/titan23_neuron_scaled_present_factor{args.factor}_pipeline_v1_2026-10-15'
    initial_limit=(8 if (out/'model_terminal.json').exists() else 20)*2**30
    gate=memory_admission(initial_limit,int(Path('/sys/fs/cgroup/memory.current').read_text()),int(Path('/sys/fs/cgroup/memory.max').read_text()))
    if not gate['admitted']:raise RuntimeError('Full neuron stage not launched: shared memory admission unavailable')
    final=read(FINAL);assert final['all_pass'] and final['all_original_connections']==77106 and final['all_events_and_round_metadata_identical']
    assert read(ORIGINAL/'pipeline_terminal.json')['all_stages_completed']
    assert read(ORIGINAL/'exact_reference_parity.json')['all_complete_frames_byte_equal']
    corruption=read(R/'experiments/scaled_present_full_audit_corruption_v1_2026-10-15/verification.json');assert corruption['all_pass']
    comparison=read(R/'experiments/xtea_scaled_present_full_comparison_v1_2026-10-15/research_decision_v1.json');assert comparison['all_frozen_factors_reported']
    if args.factor>1:
        assert read(Path(pre['required'][-1 if args.factor==2 else -2]))['all_events_and_round_metadata_equal']
    if args.factor==4:assert read(Path(pre['required'][-1]))['all_stages_completed']
    bindings=closure([Path(__file__),*[R/'tools'/s for s in SCRIPTS]])
    for path in [Path(p) for p in pre['required']]+[R/'experiments/neuron_scaled_present_ablation_prereg_v1_2026-10-15/protocol.json']:
        data=read(path)
        for p,h in data.get('bindings',{}).items():
            assert p not in bindings or bindings[p]==h
            bindings[p]=h
        bindings[str(path)]=sha(path)
    assert all(sha(p)==h for p,h in bindings.items())
    out=R/f'experiments/titan23_neuron_scaled_present_factor{args.factor}_pipeline_v1_2026-10-15'
    if not out.exists():
        out.mkdir()
        write(out/'protocol.json',dict(bindings=bindings,present_factor=args.factor,original_nodes=3593250,original_edges=39165143,connections=77106,nets=50767,rounds=2,heldout=False,native_route_labels_used_by_model=False,policy='Complete frozen present-factor development ablation; original floors, budgets, two full NET rounds, retained primary, fallback and all gates. No timeout cancellation or partial-demand success. Every stage has its own actual address-space cap and fresh 8 GiB shared margin.'))
    else:assert read(out/'protocol.json')['bindings']==bindings
    model=out/'model';ep=R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json';base=R/'experiments/titan23_neuron_node_base_wide_v1_2026-10-13/verification.json';crit=R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality'
    stages=[('model',[SCRIPTS[0],str(ep),str(model),str(base),str(crit),str(args.factor)]),('initial_audit',[SCRIPTS[1],str(model),'initial',str(model/'initial_physical_verification.json')]),('sketch_audit',[SCRIPTS[1],str(model),'sketch',str(model/'sketch_physical_verification.json')]),('event_audit',[SCRIPTS[2],str(model),'neuron',str(model/'verification.json'),str(args.factor)])]
    for name,cmd in stages:
        terminal=out/(name+'_terminal.json');action=stage_action(read(terminal) if terminal.exists() else None,(out/(name+'_process.json')).exists() or (out/(name+'.log')).exists())
        if action=='done':continue
        if action!='launch':raise RuntimeError(f'No stage restart: {name}: {action}')
        assert all(sha(p)==h for p,h in bindings.items())
        limit=(20 if name=='model' else 8)*2**30
        admission=memory_admission(limit,int(Path('/sys/fs/cgroup/memory.current').read_text()),int(Path('/sys/fs/cgroup/memory.max').read_text()))
        write(out/(name+'_admission_'+str(time.time_ns())+'.json'),admission)
        if not admission['admitted']:raise RuntimeError('Stage deferred: insufficient memory; completed stages preserved')
        tick=time.perf_counter()
        with (out/(name+'.log')).open('x') as log,(out/(name+'_memory.jsonl')).open('x') as samples:
            child=subprocess.Popen([sys.executable,str(R/'tools'/cmd[0]),*cmd[1:]],cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_AS,(limit,limit)))
            write(out/(name+'_process.json'),dict(pid=child.pid,args=child.args,address_space_limit_bytes=limit,start_stat=Path(f'/proc/{child.pid}/stat').read_text()))
            print('NEURON SCALED START',args.factor,name,child.pid,flush=True)
            while child.poll() is None:
                try:
                    mem={k:int(v.split()[0]) for line in Path(f'/proc/{child.pid}/status').read_text().splitlines() if ':' in line for k,v in [line.split(':',1)] if k in ('VmRSS','VmSize','VmHWM')}
                    samples.write(json.dumps(dict(seconds=time.perf_counter()-tick,**mem))+'\n');samples.flush()
                except FileNotFoundError:pass
                time.sleep(5)
        write(terminal,dict(exit_status=child.returncode,seconds=time.perf_counter()-tick,address_space_limit_bytes=limit))
        if child.returncode:raise SystemExit(child.returncode)
    assert all(sha(p)==h for p,h in bindings.items())
    ensure(out/'pipeline_terminal.json',dict(exit_status=0,all_stages_completed=True))
    final_gate=memory_admission(8*2**30,int(Path('/sys/fs/cgroup/memory.current').read_text()),int(Path('/sys/fs/cgroup/memory.max').read_text()))
    write(out/('final_admission_'+str(time.time_ns())+'.json'),final_gate)
    if not final_gate['admitted']:raise RuntimeError('Final parity deferred: insufficient memory; completed stages preserved')
    resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
    oldp=read(ORIGINAL/'model/protocol.json');newp=read(model/'protocol.json')
    assert newp['present_factor']==args.factor
    assert {k:v for k,v in oldp.items() if k not in ('bindings','present_cost_policy')}=={k:v for k,v in newp.items() if k not in ('bindings','present_cost_policy','present_factor')}
    for n in ('initial.json','floors.json'):assert sha(model/n)==sha(ORIGINAL/'model'/n)
    if args.factor==1:
        for n in FRAMES:assert sha(model/n)==sha(ORIGINAL/'model'/n)
        ref=read(ORIGINAL/'model/receipt.json');digests=event_digest(ref);del ref;gc.collect()
        actual=read(model/'receipt.json');assert event_digest(actual)==digests;del actual;gc.collect()
        ensure(out/'exact_reference_parity.json',dict(all_complete_frames_byte_equal=True,all_events_and_round_metadata_equal=True,complete_round_event_digests=digests))
    proof=read(model/'verification.json');assert proof['present_factor']==args.factor and proof['completed']==77106 and proof['events']==101534
    ensure(out/'development_admission.json',dict(all_stages_completed=True,present_factor=args.factor,original_initial_and_floors_byte_equal=True,full_original_connections=77106,final_overflow=proof['overflow_units'],quality_improvement_proven=False,promoted=False))


if __name__=='__main__':main()
