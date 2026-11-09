"""Preserve failed legacy-format auditor; independently audit unchanged wide run."""
import json
import subprocess
import sys
import time
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure

def main():
    run=R/'experiments/xtea_wide_retained_pipeline_v2_2026-10-13';model=run/'model'
    out=R/'experiments/xtea_wide_payload_audit_recovery_v1_2026-10-13';out.mkdir(exist_ok=False)
    script=R/'tools/verify_criticality_retained_tree_full_schedule_wide_v1.py'
    legacy=R/'tools/verify_criticality_retained_tree_full_schedule_v1.py'
    a=legacy.read_text();old='from audit_structural_node_base_v1 import audit as audit_node_base'
    assert a.count(old)==1 and a.replace(old,'from audit_wide_node_base_adapter_v1 import audit as audit_node_base')==script.read_text()
    receipt=json.loads((model/'receipt.json').read_text())
    bindings={**closure([Path(__file__),script]),**receipt['bindings'],**receipt['files'],str(model/'receipt.json'):sha(model/'receipt.json')}
    for name in ['model_terminal.json','initial_audit_terminal.json','sketch_audit_terminal.json']:
        p=run/name;assert json.loads(p.read_text())['exit_status']==0;bindings[str(p)]=sha(p)
    failed=run/'event_audit_terminal.json';log=run/'event_audit.log'
    assert json.loads(failed.read_text())['exit_status']==1
    assert 'FileNotFoundError' in log.read_text() and 'node_base.u64' in log.read_text()
    bindings[str(failed)]=sha(failed);bindings[str(log)]=sha(log)
    reference=R/'experiments/xtea_design_scoped_retained_pipeline_v1_2026-10-13/model'
    ref=json.loads((reference/'receipt.json').read_text())
    bindings.update(ref['bindings']);bindings[str(reference/'receipt.json')]=sha(reference/'receipt.json')
    assert all(sha(p)==h for p,h in bindings.items())
    (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,
        preserved_failure='Original legacy event auditor expects node_base.u64; wide payload is node_base.u128le. Model and both physical audits exited zero.',
        change='Only event auditor node-base audit import replaced; independent full XML and binary32 bit/payload audit before cost return. Every event/guard/objective/ledger check unchanged.',
        model_rerun=False),indent=2)+'\n')
    tick=time.perf_counter()
    with (out/'event_audit.log').open('x') as log:
        code=subprocess.call([sys.executable,str(script),str(model),'xtea',str(out/'event_verification.json')],cwd=R,stdout=log,stderr=subprocess.STDOUT)
    (out/'event_audit_terminal.json').write_text(json.dumps(dict(exit_status=code,seconds=time.perf_counter()-tick))+'\n')
    if code:raise SystemExit(code)
    evidence=json.loads((out/'event_verification.json').read_text())
    assert evidence['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
    assert all(sha(p)==h for p,h in evidence['bindings'].items())
    frames=['initial.json','floors.json','round0.json','round1.json','sketch.json']
    for name in frames:
        assert sha(model/name)==sha(reference/name)
        bindings[str(reference/name)]=sha(reference/name)
    assert len(ref['rounds'])==len(receipt['rounds'])==2
    for a,b in zip(ref['rounds'],receipt['rounds']):
        assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
    bindings[str(out/'event_verification.json')]=sha(out/'event_verification.json')
    assert all(sha(p)==h for p,h in bindings.items())
    result=dict(bindings=bindings,complete_wide_payload_model_physical_event_recovery_pass=True,
                all_complete_frames_byte_equal=True,all_events_and_round_metadata_equal=True,
                original_failed_event_auditor_preserved=True,model_rerun=False,
                scope='Complete exposed XTEA model using wide base loader and wide search ABI; all states/events equal original. Separate adapted independent audit closure, not original pipeline success; no Titan full-model or speed claim.')
    (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('WIDE PAYLOAD FULL MODEL AND RECOVERED AUDIT EXACT PARITY PASS',flush=True)

if __name__=='__main__':main()
