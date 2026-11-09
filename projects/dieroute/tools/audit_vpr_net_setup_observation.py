"""Check observed VPR setup decisions only after five native compatibility runs pass."""
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    base=args.build.resolve()
    assert not args.output.exists()
    native_path=base/'native_compatibility_audit.json'
    native=json.loads(native_path.read_text())
    assert native['status']=='five_repeat_source_bound_vpr_native_baseline_compatibility_audited'
    assert native['numerical_and_canonical_compatibility'] and len(native['cases'])==5
    manifest_path=base/'manifest.json'
    manifest=json.loads(manifest_path.read_text())
    assert set(manifest['post_patch_source_sha256'])=={'source_vtr/vpr/src/route/route_net.cpp'}
    assert sha(base/'source_vtr/vpr/src/route/route_net.cpp')==next(iter(manifest['post_patch_source_sha256'].values()))
    fields=('iteration','net_id','fanout','action','had_incumbent','old_remaining','new_remaining','first_iteration','hold_ripup')
    files=[native_path,manifest_path,base/'source_manifest.json',base/'build_dependency_audit.json',
           base/'applied_net_setup_observation.patch',Path(__file__).resolve()]
    canonical=None
    for case in native['cases']:
        directory=Path(case['run'])
        log=directory/'vpr.log'
        assert sha(log)==native['source_sha256'][str(log)]
        values=re.findall(r'^DIEROUTE_SETUP,([0-9,]+)$',log.read_text(),re.MULTILINE)
        assert values,'No actual setup records'
        rows=[]
        for value in values:
            numbers=list(map(int,value.split(',')))
            assert len(numbers)==len(fields)
            rows.append(dict(zip(fields,numbers)))
        if canonical is None:
            canonical=rows
        else:
            assert rows==canonical,'Setup execution differs across repeats'
        files.append(log)
    epochs=defaultdict(list)
    assert [r['iteration'] for r in canonical]==sorted(r['iteration'] for r in canonical)
    for row in canonical:
        epochs[row['iteration']].append(row)
        assert row['iteration']>=1 and row['action'] in (0,1,2)
        assert all(row[k] in (0,1) for k in ('had_incumbent','first_iteration','hold_ripup'))
        assert row['first_iteration']==int(row['iteration']==1)
        assert 0<=row['old_remaining']<=row['fanout'] and 0<=row['new_remaining']<=row['fanout']
        if not row['had_incumbent']:
            assert row['old_remaining']==row['fanout']
        whole_reset=row['fanout']<16 or row['first_iteration'] or row['hold_ripup']
        assert (row['action']==0)==bool(whole_reset)
        if row['action'] in (0,2):
            assert row['new_remaining']==row['fanout']
    summaries=[]
    for epoch,rows in sorted(epochs.items()):
        fanouts=[r['fanout'] for r in rows]
        assert fanouts==sorted(fanouts,reverse=True),'Actual setup calls violate serial fanout ordering'
        actions=Counter(r['action'] for r in rows)
        partial=[r for r in rows if r['action']==1]
        summaries.append(dict(iteration=epoch,setup_calls=len(rows),unique_nets=len({r['net_id'] for r in rows}),
                              whole_reset_calls=actions[0],partial_prune_calls=actions[1],fully_pruned_calls=actions[2],
                              partial_prune_calls_with_retained_sink_flags=sum(r['new_remaining']<r['fanout'] for r in partial),
                              retained_sink_flag_occurrences=sum(r['fanout']-r['new_remaining'] for r in partial)))
    events=args.output.with_suffix('.events.csv')
    with events.open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        writer.writerows(canonical)
    files.append(events)
    totals={k:sum(r[k] for r in summaries) for k in ('setup_calls','whole_reset_calls','partial_prune_calls',
             'fully_pruned_calls','partial_prune_calls_with_retained_sink_flags','retained_sink_flag_occurrences')}
    report=dict(status='five_repeat_canonical_compatible_native_setup_observations_audited',
                repeats=5,per_iteration=summaries,totals=totals,
                source_sha256={str(p):sha(p) for p in files},
                scope='Actual whole-net setup boundary records, including terminal iteration calls. '
                      'Only route_net.cpp logging changed; complete native compatibility required. '
                      'Sink occurrences count flags surviving partial prune,not unique connections, '
                      'saved searches, electrical branch-by-branch proof,a counterfactual quality effect '
                      'or physical performance. Does not reproduce the complete VPR search/control trace.',
                board_result=False,research_complete=False)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],totals=totals)))
