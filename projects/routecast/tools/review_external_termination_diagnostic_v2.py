"""Review all6 fixed stop-policy cells; preserve original cohort failure."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_termination_diagnostic_v1_2026-10-19';P=R/'experiments/prospective_external_family_executable_development_v1_2026-10-19'
def main():
    terminal=D/'execution/terminal.json'
    if not terminal.exists():raise SystemExit('NOT_READY: fixed six-case diagnostic still running')
    end=json.loads(terminal.read_text());assert end['status']=='ALL6_FIXED_TERMINATION_DIAGNOSTICS_TERMINAL' and len(end['rows'])==6
    manifest=D/'manifest.json';m=json.loads(manifest.read_text());bindings={str(p):sha(p) for p in [terminal,manifest,Path(__file__).resolve()]};rows=[]
    for job in m['cases']:
        d=Path(job['output']);proof=d/'verification.json';v=json.loads(proof.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());bindings[str(proof)]=sha(proof)
        log=(d/'native.log').read_text();iterations=[]
        for line in log.splitlines():
            match=re.match(r'^\s*(\d+)\s+[0-9.]+\s+[0-9.]+\s+\d+\s+\S+\s+\d+\s+\d+\s+(\d+)\s+\(',line)
            if match:iterations.append((int(match[1]),int(match[2])))
        row=dict(case=job['case'],width=job['width'],policy=job['termination_policy'],native_exit_code=v['exit_status'],status=v['status'],last_iteration=iterations[-1][0] if iterations else None,last_iteration_overused_nodes=iterations[-1][1] if iterations else None,passed_FULL_physical_canonical=v['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS')
        if job['width']==160 and 'noearly_100/' in job['case']:
            old=P/'native/w160/source';row['unchanged_guard_path_same_failed_output_bytes']={name:sha(d/name)==sha(old/name) for name in ('output.route',)}
        rows.append(row)
    result=dict(status='ALL6_FIXED_TERMINATION_DIAGNOSTIC_REVIEW',bindings=bindings,rows=rows,original_all9_cohort_availability_gate_pass=False,primary_cohort_replaced=False,model_quality_or_utility_evaluated=False,strict_unseen_admitted=False,scope='New fixed source termination settings only. Success after changed stop policy does not retroactively pass original cohort, prove infeasibility of failed cells, independent causality of all knobs, forecast quality or complete-flow gain.')
    with (D/'review_v2.json').open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
