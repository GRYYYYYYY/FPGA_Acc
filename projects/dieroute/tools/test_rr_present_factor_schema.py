"""Check generic preset validation against existing actual-host factor traces."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from audit_rr_present_experiments import verify_present_factors
import audit_rr_present_experiments


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('fixture',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    files=[Path(__file__).resolve(),Path(audit_rr_present_experiments.__file__).resolve()]
    cases=[]
    for mode in range(3):
        path=args.fixture.resolve()/f'mode{mode}_issue4.iterations.csv'
        with path.open() as stream:
            rows=list(csv.DictReader(stream))
        verify_present_factors(rows,mode)
        cases.append(dict(mode=mode,case='actual_host_factors',passed=True,epochs=len(rows)))
        for name in ('changed_first_transition','missing_epoch'):
            corrupt=[dict(row) for row in rows]
            if name=='missing_epoch':
                corrupt.pop(1)
            else:
                corrupt[1]['present_factor_q']=str(int(corrupt[1]['present_factor_q'])+1)
            try:
                verify_present_factors(corrupt,mode)
            except ValueError:
                cases.append(dict(mode=mode,case=name,rejected=True))
            else:
                raise AssertionError('Corrupt preset passed')
        files.append(path)
    report=dict(status='three_actual_host_factor_traces_and_six_schema_corruptions_checked',cases=cases,
                source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                scope='Generic present-factor schema only, using archived real small-graph host outputs; '
                      'not another routing run or complete five-repeat native audit.',board_result=False,research_complete=False)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],cases=len(cases))))
