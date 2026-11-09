"""Retain all nine prespecified targets, including unavailable comparisons."""
import argparse,json
from pathlib import Path
from pre_route_endpoints import sha

def summarize(spec,output):
    s=json.loads(Path(spec).read_text());rows=[];bindings={str(Path(spec).resolve()):sha(spec)}
    if len(s['cases'])!=9 or len({r['case'] for r in s['cases']})!=9:raise ValueError('fixed9 case universe')
    for row in s['cases']:
        r=dict(case=row['case'],available=False,pass_case_gate=False)
        try:
            path=Path(row['comparison']);d=json.loads(path.read_text())
            if d['status']!='COMPLETE_FIXED_CASE_FORECAST_COMPARISON' or d['case']!=row['case']:raise ValueError('case/result mismatch')
            if not all(sha(p)==h for p,h in d['bindings'].items()):raise ValueError('comparison evidence changed')
            bindings.update(d['bindings']);bindings[str(path)]=sha(path);r.update(available=True,pass_case_gate=d['pass_case_gate'],checks=d['checks'])
        except Exception as e:r['error']=repr(e)
        rows.append(r)
    result=dict(status='FIXED9_FORECAST_COHORT_REVIEW',bindings=bindings,rows=rows,all9_available=all(r['available'] for r in rows),all9_primary_gate_pass=all(r['available'] and r['pass_case_gate'] for r in rows),strict_unseen_admitted=False,candidate_promoted=False,complete_workflow_gain_proven=False)
    with Path(output).open('x') as f:json.dump(result,f,indent=2)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('spec');p.add_argument('output');a=p.parse_args();summarize(a.spec,a.output)
