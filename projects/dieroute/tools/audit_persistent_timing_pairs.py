"""Independently audit completed alternating host-CPU timing pairs and raw artifacts."""
import argparse,json,statistics,math
from pathlib import Path
from persistent_vpr_timing import sha

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('protocol',type=Path);a=p.parse_args()
    directory=a.directory.resolve();protocol=a.protocol.resolve();manifest=directory/'manifest.json'
    m=json.loads(manifest.read_text());pr=json.loads(protocol.read_text())
    assert m['status']=='five_alternating_cpu_pairs_complete_all_artifacts_audited' and m['pairs']==5
    for mapping in (m['source_sha256'],pr['source_sha256']):
        assert all(sha(Path(name))==digest for name,digest in mapping.items())
    assert len(m['records'])==10
    pair_path=next(Path(name) for name in m['source_sha256'] if name.endswith('/pair.json'))
    pair=json.loads(pair_path.read_text());mode,=pair['modes'];epochs=pair['modes'][mode]['runs'][0]['iterations']
    counts=[];ratios=[];sources={str(manifest):sha(manifest),str(protocol):sha(protocol)}
    for index in range(5):
        rows=m['records'][index*2:index*2+2]
        assert [r['transport'] for r in rows]==(['fresh','persistent'] if index%2==0 else ['persistent','fresh'])
        assert all(r['pair']==index and r['returncode']==0 and r['status']=='completed_and_artifacts_audited' and r['outer_elapsed_ns']>0 for r in rows)
        times={}
        for r in rows:
            case=directory/f"pair_{index}_{r['transport']}"
            audit_path=case/'equivalence_audit.json';audit=json.loads(audit_path.read_text())
            assert sha(audit_path)==r['audit_sha256']
            assert audit['status']=='online_router_all_reference_artifacts_equivalent_except_wall_ms' and audit['epochs']==epochs
            assert len(audit['checks'])==66
            for check in audit['checks']:
                original=pair_path.parent/(mode+'_0'+check['suffix']);actual=case/('route'+check['suffix'])
                assert sha(original)==check['reference_sha256'] and sha(actual)==check['online_sha256']
                if check['suffix']=='.json':
                    left=json.loads(original.read_text());right=json.loads(actual.read_text());left.pop('wall_ms');right.pop('wall_ms');assert left==right
                else:assert original.read_bytes()==actual.read_bytes()
            if r['transport']=='persistent':
                case_manifest=json.loads((case/'manifest.json').read_text())
                assert case_manifest['requests']==epochs and case_manifest['cold_start_through_shutdown_ns']<=r['outer_elapsed_ns']
                receipts=[json.loads(line) for line in (case/'timing_session/receipts.jsonl').read_text().splitlines()]
                responses=[v for v in receipts if v['event']=='timing_response']
                assert len(responses)==epochs and [v['epoch'] for v in responses]==list(range(epochs))
                assert [v['sequence'] for v in responses]==list(range(epochs))
                assert receipts[-1]['event']=='session_stop' and receipts[-1]['returncode']==0
                assert len([v for v in receipts if v['event']=='engine_ready'])==1
                assert all(sha(Path(v['input']))==v['input_sha256'] and sha(Path(v['output']))==v['output_sha256'] for v in responses)
            times[r['transport']]=r['outer_elapsed_ns']
            sources[str(audit_path)]=sha(audit_path);counts.append(len(audit['checks']))
        ratios.append(times['fresh']/times['persistent'])
    assert ratios==m['paired_ratios']
    report=dict(status='five_cpu_pairs_independently_audited',paired_fresh_over_persistent_ratios=ratios,median_paired_ratio=statistics.median(ratios),geometric_mean_ratio=math.exp(statistics.mean(math.log(x) for x in ratios)),range_ratio=[min(ratios),max(ratios)],runs=10,artifact_comparisons=sum(counts),source_sha256=sources,limitations='One development design,shared host,concurrent jobs,no cache flushing or isolated core allocation. Cold process startup included;disk caches may be warm. No population significance or physical FPGA speed/energy inference.',board_result=False,research_complete=False)
    context=directory/'shared_host_context.json'
    if context.exists():report['shared_host_context']=json.loads(context.read_text());report['source_sha256'][str(context)]=sha(context)
    (directory/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
