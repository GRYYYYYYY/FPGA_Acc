"""Evaluate fixed zero-first settings on every declared development case without filtering failures."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cohort',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    base=args.cohort.resolve()
    assert not args.output.exists()
    protocol_path=base/'protocol.json'
    protocol=json.loads(protocol_path.read_text())
    files=[protocol_path,Path(__file__).resolve()]
    ex_path=Path(protocol['reuse_ex5p_result'])
    ex=json.loads(ex_path.read_text())
    assert ex['status']=='three_arm_present_study_complete_zero_first_passes_ex5p_architecture_model_quality_checks'
    assert all(sha(Path(p))==h for p,h in ex['source_sha256'].items())
    rows={'ex5p':ex['outcomes']['zero_first_warm_start']}
    files.append(ex_path)
    timing_paths=[base/'ex5p_candidate_timing/audit.json']
    for case in protocol['cases']:
        name=case['name']
        directory=base/name
        comparison_path=directory/'paired_comparison.json'
        comparison=json.loads(comparison_path.read_text())
        assert comparison['status']=='same_source_present_schedule_development_pair_audited'
        assert all(sha(Path(p))==h for p,h in comparison['source_sha256'].items())
        audit_path=directory/'routing_audit_2.json'
        audit=json.loads(audit_path.read_text())['experiments'][0]
        result=audit['modes']['downstream_bounded']
        assert result==comparison['outcomes']['zero_first_warm_start']['downstream_bounded']
        assert result['repeats_verified']==5
        baseline=audit['native_model_crossings']
        q=result.get('native_qor')
        flags=dict(native_legal=result['status']=='passed' and bool(result['counters']['legal']),
                   wirelength_nondegrade=q is not None and q['total_wirelength']<=q['baseline_wirelength'],
                   cpd_nondegrade=q is not None and q['critical_path_delay_ns']<=q['baseline_cpd_ns'],
                   model_crossing_edges_nondegrade=result.get('final_net_crossing_edges',10**9)<=baseline['net_crossing_edges'],
                   model_crossing_destinations_nondegrade=result.get('final_net_crossing_destinations',10**9)<=baseline['net_crossing_destinations'])
        rows[name]=dict(native_qor=q,iterations=result['counters']['iterations'],expanded=result['counters']['expanded'],
                        baseline_model_crossings=baseline,final_net_crossing_edges=result.get('final_net_crossing_edges'),
                        final_net_crossing_destinations=result.get('final_net_crossing_destinations'),checks=flags,
                        architecture_model_checks_pass=all(flags.values()))
        native_path=directory/'native_compatibility_audit.json'
        native=json.loads(native_path.read_text())
        assert native['numerical_and_canonical_compatibility'] and len(native['cases'])==5
        files.extend([comparison_path,audit_path,native_path])
        timing_paths.append(directory/'candidate_timing/audit.json')
    assert set(rows)=={'ex5p','diffeq','alu4'}
    for timing_path in timing_paths:
        proof=json.loads(timing_path.read_text())
        assert proof['all_epoch_outputs_byte_equivalent']
        assert all(c['byte_equivalent'] for c in proof['epochs'])
        files.append(timing_path)
    passed=all(all(row['checks'].values()) for row in rows.values())
    report=dict(status='fixed_present_preset_development_cohort_audited',
                all_development_architecture_model_checks_pass=passed,cases=rows,
                source_sha256={str(p):sha(p) for p in files},
                scope='All three declared development cases retained,including failed candidates. '
                      'Two new cases have same-source preset0/2 controls,five-repetition native/source-bound '
                      'baseline compatibility,state/version replay and rehashed-corruption campaigns. '
                      'Source-bound timing hook reproduces every candidate first-repeat epoch CSV. '
                      'Model crossing counts are not commercialphysicalSLL. Not heldout generalization, '
                      'multi-seed/scaling evidence,productiondefault adoption,fullG4orG1-G8completion, '
                      'physicalperformance orcongestion-algorithmnovelty.',board_result=False,research_complete=False)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],all_development_model_checks_pass=passed)))
