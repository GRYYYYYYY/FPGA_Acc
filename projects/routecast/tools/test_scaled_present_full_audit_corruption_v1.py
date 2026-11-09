"""Run the real full XML/Fraction auditor against corrupted complete XTEA receipts."""
import copy, datetime, json, resource, subprocess, sys, time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from observe_neuron_compiled_pipeline_v1 import snapshot


def main():
    original=R/'experiments/xtea_scaled_present_factor1_pipeline_v1_2026-10-15'
    assert json.loads((original/'pipeline_terminal.json').read_text())['all_stages_completed']
    assert json.loads((original/'exact_reference_parity.json').read_text())['all_events_and_round_metadata_equal']
    out=R/'experiments/scaled_present_full_audit_corruption_v1_2026-10-15'
    out.mkdir()
    audit=R/'tools/verify_scaled_present_retained_tree_full_schedule_v1.py'
    src=original/'model'
    results=[]
    for case in ('objective_plus_one','factor2_mislabel','epoch_plus_one'):
        live=snapshot()
        reserve=20*2**30
        if live['model']['verified_live']:
            lines=Path('/proc/1075109/status').read_text().splitlines()
            vm=int(next(x for x in lines if x.startswith('VmSize:')).split()[1])*1024
            reserve=max(0,20*2**30-vm)
        elif live['stages']['model']['terminal']['observed']:reserve=0
        free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text())
        required=reserve+9*2**30
        admission=dict(case=case,shared_headroom_bytes=free,required_bytes=required,child_cap_bytes=2**30,admitted=free>=required)
        (out/(case+'_admission.json')).write_text(json.dumps(admission,indent=2)+'\n')
        if free<required:raise RuntimeError('Fresh memory admission unavailable; no audit launched')
        fixture=out/case;fixture.mkdir()
        for n in ('initial.json','sketch.json'):
            (fixture/n).symlink_to(src/n)
        receipt=json.loads((src/'receipt.json').read_text())
        protocol=json.loads((src/'protocol.json').read_text())
        factor=1
        if case=='objective_plus_one':
            event=next(e for row in receipt['rounds'] for e in row['events'] if 'objective_guard' in e)
            from fractions import Fraction
            event['objective_guard']['old_score']=str(Fraction(event['objective_guard']['old_score'])+1)
        elif case=='factor2_mislabel':protocol['present_factor']=factor=2
        else:receipt['rounds'][0]['events'][0]['old_epoch']+=1
        (fixture/'protocol.json').write_text(json.dumps(protocol)+'\n')
        (fixture/'receipt.json').write_text(json.dumps(receipt)+'\n')
        log=out/(case+'.log');tick=time.perf_counter()
        with log.open('x') as f:
            rc=subprocess.call([sys.executable,str(audit),str(fixture),'xtea',str(fixture/'verification.json'),str(factor)],cwd=R,stdout=f,stderr=subprocess.STDOUT,preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_AS,(2**30,2**30)))
        tail=log.read_text().splitlines()[-5:]
        # Require semantic assertion rejection, not OOM, import or I/O failure.
        assert rc==1 and tail[-1]=='AssertionError' and not (fixture/'verification.json').exists(),(case,rc,tail)
        results.append(dict(case=case,exit_status=rc,seconds=time.perf_counter()-tick,tail=tail,receipt_sha256=sha(fixture/'receipt.json'),protocol_sha256=sha(fixture/'protocol.json')))
        print('PASS semantic corruption rejection',case,flush=True)
    result=dict(checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bindings={**closure([Path(__file__)]),str(audit):sha(audit),str(original/'exact_reference_parity.json'):sha(original/'exact_reference_parity.json')},all_pass=True,cases=results,scope='Real complete XTEA XML/Fraction schedule auditor rejects changed objective, wrong factor interpretation and old epoch. Original model files unchanged. No higher-factor full-design quality claim.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
