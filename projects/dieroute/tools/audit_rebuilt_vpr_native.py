"""Check five fresh native runs against an unchanged historical VPR baseline."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('historical',type=Path)
    parser.add_argument('build_audit',type=Path)
    parser.add_argument('runs',type=Path,nargs=5)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    historical,proof_path=args.historical.resolve(),args.build_audit.resolve()
    proof=json.loads(proof_path.read_text())
    assert proof['status']=='new_frozen_vpr_sources_compiler_dependencies_and_link_inputs_audited'
    for key in ('source_sha256','dependency_sha256','explicit_link_input_sha256',
                'runtime_library_sha256','compiled_object_sha256'):
        assert all(sha(Path(p))==h for p,h in proof[key].items()),key
    assert sha(Path(proof['binary']))==proof['binary_sha256']
    old=json.loads((historical/'run.json').read_text())

    def metrics(directory):
        text=(directory/'vpr.log').read_text()
        assert 'RouterOpts.check_route: FULL' in text
        assert 'Circuit successfully routed with a channel width factor of 80.' in text
        return dict(wirelength=int(re.findall(r'Total wirelength:\s+(\d+)',text)[-1]),
                    cpd_ns=float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)[-1]))

    def graph_digest(path):
        root=ET.parse(path).getroot()
        removed={key:root.attrib.pop(key) for key in ('tool_version','tool_comment') if key in root.attrib}
        return hashlib.sha256(ET.tostring(root)).hexdigest(),removed

    def verify_run(directory):
        record=json.loads((directory/'run.json').read_text())
        assert record['status']=='passed' and record['returncode']==0
        assert all(sha(directory/p)==meta['sha256'] for p,meta in record['artifacts'].items())
        return record

    verify_run(historical)
    original_metrics=metrics(historical)
    canonical=('circuit.net','circuit.net.post_routing','circuit.place','circuit.route')
    original_hashes={name:sha(historical/name) for name in canonical}
    original_graph,old_metadata=graph_digest(historical/'rr_graph.xml')
    cases=[]
    files=[proof_path,historical/'run.json',Path(__file__).resolve()]
    for directory in [p.resolve() for p in args.runs]:
        record=verify_run(directory)
        assert record['sources']['vpr']['path']==proof['binary']
        assert record['sources']['vpr']['sha256']==proof['binary_sha256']
        assert record['command'][1:]==old['command'][1:]
        for kind in ('arch','circuit'):
            assert record['sources'][kind]['sha256']==old['sources'][kind]['sha256']
        observed=metrics(directory)
        artifacts={name:sha(directory/name) for name in canonical}
        graph,metadata=graph_digest(directory/'rr_graph.xml')
        cases.append(dict(run=str(directory),metrics=observed,canonical_sha256=artifacts,
                          rr_graph_structural_sha256=graph,excluded_graph_tool_metadata=metadata,
                          historical_metrics_equal=observed==original_metrics,
                          historical_canonical_artifacts_equal=artifacts==original_hashes,
                          historical_rr_graph_equal=graph==original_graph))
        files.extend([directory/'run.json',directory/'vpr.log',*[directory/n for n in canonical],directory/'rr_graph.xml'])
    assert all((r['metrics'],r['canonical_sha256'],r['rr_graph_structural_sha256'])==
               (cases[0]['metrics'],cases[0]['canonical_sha256'],cases[0]['rr_graph_structural_sha256']) for r in cases)
    compatible=all(r['historical_metrics_equal'] and r['historical_canonical_artifacts_equal'] and r['historical_rr_graph_equal'] for r in cases)
    report=dict(status='five_repeat_source_bound_vpr_native_baseline_compatibility_audited',
                numerical_and_canonical_compatibility=compatible,cases=cases,
                historical_metrics=original_metrics,historical_canonical_sha256=original_hashes,
                historical_rr_graph_structural_sha256=original_graph,
                historical_excluded_graph_tool_metadata=old_metadata,
                source_sha256={str(p):sha(p) for p in files},
                scope='Five full native architecture-model runs with explicit FULL route checks, same '
                      'architecture/circuit/options/seed/worker count, fresh-source compiler dependency '
                      'audit and deterministic canonical outputs. RR graph comparison excludes only root '
                      'tool_version/tool_comment. This new source-bound baseline does not recover the old '
                      'binary as-built sources, replace its stronger reference, prove cross-case quality '
                      'or establish physical board timing/performance.',board_result=False,research_complete=False)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],compatible=compatible,repeats=len(cases))))


if __name__=='__main__':
    main()
