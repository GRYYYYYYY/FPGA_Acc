"""Check full timing coverage and nested stage accounting after terminal repeat."""
import hashlib,json
from pathlib import Path


def main():
    D=Path('work/native_implicit_compound_repeat_v2_20261017')
    manifest=D/'manifest.json';state=json.loads(manifest.read_text())
    assert state['status']=='three_case_compound_repeat_terminal_requires_independent_review'
    assert len(state['cases'])==3 and len(state['stages'])==21
    outcomes=[]
    for case in state['cases']:
        stages=[s for s in state['stages'] if s['case']==case['case']]
        assert len(stages)==7 and all(s['status']=='terminal' and s.get('returncode',0)==0 for s in stages)
        assert {s['label'] for s in stages}=={case['case']+'_feedback_off'+suffix for suffix in ['', '_tree','_timing','_write','_validate']}|{'sweep','refresh'}
        duration=sum(s['wall_ns'] for s in stages);assert 0<=duration<=case['wall_ns']
        bylabel={s['label']:s['wall_ns'] for s in stages}
        checks=sum(s['wall_ns'] for s in stages if s['label'].endswith(('_tree','_timing')))
        outcomes.append(dict(case=case['case'],full_case_wall_ns=case['wall_ns'],stage_wall_ns=bylabel,
                             explicit_parent_tree_and_provenance_audit_ns=checks,
                             interstage_overhead_ns=case['wall_ns']-duration,
                             algorithm_and_native_validation_plus_overhead_ns=case['wall_ns']-checks))
    total=sum(c['wall_ns'] for c in state['cases']);assert total<=state['wall_ns']
    inputs=[manifest,D/'protocol.json',Path(__file__)]
    result=dict(status='terminal_compound_stage_and_case_timing_partitions_checked',cases=outcomes,
                full_run_wall_ns=state['wall_ns'],between_case_overhead_ns=state['wall_ns']-total,
                source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
                scope='Full serial repeat after source-hash preflight. Parent tree and provenance checks shown separately. Native STA remains within algorithm stages; no subtraction or FPGA speedup. Shared-host execution, no confidence interval or new random seed.',research_complete=False)
    O=Path('work/native_implicit_compound_timing_review_20261017');O.mkdir(exist_ok=False)
    (O/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(outcomes))


if __name__=='__main__':main()
