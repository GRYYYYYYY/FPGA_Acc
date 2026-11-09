"""Full original neuron two-round retained model and independent physical replay.

Same frozen policy as the exposed XTEA/MMC studies. Only exact representation
changes were admitted. A fixed child address-space bound is a resource guard;
no elapsed-time stop, omitted demand or coarser electrical policy is permitted.
"""
import json
import resource
import subprocess
import sys
import time
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure

def process_memory(pid):
    try:
        lines=Path(f'/proc/{pid}/status').read_text().splitlines()
    except FileNotFoundError:return None
    return {k:int(v.split()[0]) for line in lines if ':' in line for k,v in [line.split(':',1)] if k in ['VmRSS','VmHWM','VmSize']}

def main():
    out=R/'experiments/titan23_neuron_compiled_criticality_pipeline_v1_2026-10-15'
    ep=R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json'
    base=R/'experiments/titan23_neuron_node_base_wide_v1_2026-10-13/verification.json'
    crit=R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality'
    scripts=['run_design_scoped_compiled_criticality_retained_tree_v1.py','verify_resident_demand_frame_direct_lattice_v7.py','verify_criticality_retained_tree_full_schedule_wide_v1.py']
    bindings=closure([Path(__file__),*[R/'tools'/s for s in scripts]])
    proofs=[R/'experiments/titan23_neuron_compact_graph_admission_v1_2026-10-13/verification.json',
            R/'experiments/design_wide_input_contract_v1_2026-10-13/verification.json',base.with_name('independent_verification.json'),R/'experiments/compiled_criticality_tree_contract_v1_2026-10-15/verification.json']
    for path in proofs:
        proof=json.loads(path.read_text());assert proof['all_pass']
        assert all(sha(p)==h for p,h in proof['bindings'].items())
        for p,h in proof['bindings'].items():
            assert p not in bindings or bindings[p]==h
            bindings[p]=h
        bindings[str(path)]=sha(path)
    admission=json.loads(proofs[0].read_text())
    assert (admission['nodes'],admission['edges'],admission['connections'],admission['scale'])==(3593250,39165143,77106,10**29)
    xtea=R/'experiments/xtea_compiled_criticality_retained_pipeline_v1_2026-10-15'
    parity=json.loads((xtea/'exact_reference_parity.json').read_text())
    assert parity['all_complete_frames_byte_equal'] and parity['all_events_and_round_metadata_equal']
    assert json.loads((xtea/'pipeline_terminal.json').read_text())['all_stages_completed']
    for p in [xtea/'exact_reference_parity.json',xtea/'pipeline_terminal.json',xtea/'model/receipt.json',xtea/'model/verification.json']:
        data=json.loads(p.read_text())
        for q,h in data.get('bindings',{}).items():
            assert q not in bindings or bindings[q]==h
            bindings[q]=h
        bindings[str(p)]=sha(p)
    for q,h in json.loads((xtea/'model/receipt.json').read_text())['files'].items():bindings[q]=h
    assert all(sha(p)==h for p,h in bindings.items())
    failed=R/'experiments/titan23_neuron_compact_wide_retained_pipeline_v1_2026-10-13'
    assert json.loads((failed/'model_terminal.json').read_text())['exit_status']==1
    assert 'MemoryError' in (failed/'model.log').read_text()
    assert not (failed/'model/protocol.json').exists() and not (failed/'model/initial.json').exists()
    for name in ['protocol.json','model_terminal.json','model.log','model_memory.jsonl']:
        path=failed/name;bindings[str(path)]=sha(path)
    assert all(sha(p)==h for p,h in bindings.items())
    failed_v2=R/'experiments/titan23_neuron_compact_wide_retained_pipeline_v2_2026-10-13'
    assert json.loads((failed_v2/'model_terminal.json').read_text())['exit_status']==1
    assert 'MemoryError' in (failed_v2/'model.log').read_text()
    assert (failed_v2/'model/protocol.json').exists() and not (failed_v2/'model/initial.json').exists()
    for name in ['protocol.json','model_terminal.json','model.log','model_memory.jsonl','model/protocol.json']:
        path=failed_v2/name;bindings[str(path)]=sha(path)
    assert all(sha(p)==h for p,h in bindings.items())
    limit=20*2**30;margin=8*2**30
    memory_max=int(Path('/sys/fs/cgroup/memory.max').read_text());current=int(Path('/sys/fs/cgroup/memory.current').read_text())
    if memory_max-current<limit+margin:
        raise RuntimeError(f'Not launched: shared available memory {memory_max-current} below fixed {limit+margin} admission requirement')
    out.mkdir(exist_ok=False)
    policy=dict(bindings=bindings,endpoint=str(ep),node_base_proof=str(base),criticality_directory=str(crit),
                original_nodes=3593250,original_edges=39165143,connections=77106,nets=50767,rounds=2,
                heldout_family_certified=False,native_route_labels_used=False,
                child_address_space_limit_bytes=limit,shared_memory_max_bytes=memory_max,
                shared_memory_current_at_launch_bytes=current,minimum_extra_headroom_bytes=margin,
                timeout_policy='No elapsed-time cancellation. Memory allocation failure is a recorded resource failure, never partial-demand success.',
                policy='Full allNET two-round retained primary fanout16; original floor/budget; frozen perpin initialized criticality; delayed multiplicative history; exact same fallback and strict objective/overflow transaction guards.',
                preserved_failure='v1 MemoryError before floor searches; v2 MemoryError allocating ctypes POD arrays at deferred singleton-engine initialization during initial floors. Both same 24GiB bound, no complete initial frame. Direct scalar member writes remove per-entry ctypes ownership tables; no scientific parameter change.',
                implementation_extension='Checked 256-bit compiled criticality expansion borrows already patched exact price buffers. Initial floors, retained seeding, fullNET schedule, budgets, fallbacks and all gates unchanged. Original v3 max observed VmSize 12890260 KiB plus compiled workspace fits the lower fixed 20 GiB resource cap; memory failure remains a failure.',
                representation='Direct POD cost-member writes without per-entry ownership tables, deferred engine allocation, interned equal exact costs, columnar original node subtrees, stable complete CSR, class-coded exact RC, packed immutable search IDs, two-limb costs, u128le native base, exact complete physical edge inverse.',
                scope='Complete original Titan23/neuron development transfer; independent full physical and event audits required. No native QoR, whole-family holdout, hardware, or end-to-end benefit claim.')
    (out/'protocol.json').write_text(json.dumps(policy,indent=2)+'\n')
    model=out/'model'
    stages=[('model',[scripts[0],str(ep),str(model),str(base),str(crit)]),
            ('initial_audit',[scripts[1],str(model),'initial',str(model/'initial_physical_verification.json')]),
            ('sketch_audit',[scripts[1],str(model),'sketch',str(model/'sketch_physical_verification.json')]),
            ('event_audit',[scripts[2],str(model),'neuron',str(model/'verification.json')])]
    def bounded_child():resource.setrlimit(resource.RLIMIT_AS,(stage_limit,stage_limit))
    for name,args in stages:
        assert all(sha(p)==h for p,h in bindings.items())
        stage_limit=limit if name=='model' else 8*2**30
        current=int(Path('/sys/fs/cgroup/memory.current').read_text())
        maximum=int(Path('/sys/fs/cgroup/memory.max').read_text())
        admission=dict(stage=name,shared_memory_current_bytes=current,shared_memory_max_bytes=maximum,child_limit_bytes=stage_limit,margin_bytes=margin,admitted=maximum-current>=stage_limit+margin)
        (out/(name+'_admission.json')).write_text(json.dumps(admission,indent=2)+'\n')
        if not admission['admitted']:raise RuntimeError('Stage not launched: shared memory admission unavailable')
        tick=time.perf_counter();samples=0;peak=0
        with (out/(name+'.log')).open('x') as log, (out/(name+'_memory.jsonl')).open('x') as memory_log:
            process=subprocess.Popen([sys.executable,str(R/'tools'/args[0]),*args[1:]],cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=bounded_child)
            (out/(name+'_process.json')).write_text(json.dumps(dict(pid=process.pid,args=process.args,address_space_limit_bytes=limit))+'\n')
            print('NEURON START',name,process.pid,flush=True)
            while process.poll() is None:
                sample=process_memory(process.pid)
                if sample:
                    peak=max(peak,sample.get('VmHWM',0));samples+=1
                    memory_log.write(json.dumps(dict(seconds=time.perf_counter()-tick,**sample))+'\n');memory_log.flush()
                time.sleep(5)
            code=process.returncode
        (out/(name+'_terminal.json')).write_text(json.dumps(dict(exit_status=code,seconds=time.perf_counter()-tick,sampled_peak_rss_kib=peak,samples=samples,
            memory_scope='Sampled proc VmHWM lower bound on final peak; no unobserved terminal peak claim. Fixed RLIMIT_AS applies to complete child process.'))+'\n')
        print('NEURON END',name,code,flush=True)
        if code:raise SystemExit(code)
    assert all(sha(p)==h for p,h in bindings.items())
    (out/'pipeline_terminal.json').write_text(json.dumps(dict(exit_status=0,all_stages_completed=True))+'\n')
    print('NEURON COMPLETE MODEL AND ALL INDEPENDENT AUDITS PASS',flush=True)
    reference=R/'experiments/titan23_neuron_compact_wide_retained_pipeline_v3_2026-10-13/model'
    actual=json.loads((model/'receipt.json').read_text());old=json.loads((reference/'receipt.json').read_text())
    for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:
        assert sha(model/name)==sha(reference/name),name
    assert len(actual['rounds'])==len(old['rounds'])==2
    for a,b in zip(actual['rounds'],old['rounds']):
        assert {k:v for k,v in a.items() if k not in ('seconds','state_file')}=={k:v for k,v in b.items() if k not in ('seconds','state_file')}
    (out/'exact_reference_parity.json').write_text(json.dumps(dict(reference_receipt_sha256=sha(reference/'receipt.json'),candidate_receipt_sha256=sha(model/'receipt.json'),all_complete_frames_byte_equal=True,all_events_and_round_metadata_equal=True,scope='Complete original neuron model/all physical and event audits plus exact old-model state and event parity. No paired timing, improved quality, heldout or end-to-end benefit claim.'),indent=2)+'\n')
    print('NEURON FULL ORIGINAL STATE AND EVENT EXACT PARITY PASS',flush=True)

if __name__=='__main__':main()
