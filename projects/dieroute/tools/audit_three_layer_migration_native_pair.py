"""Terminal integrity, repeat, native quality and crossing review for matched migration."""
import collections,csv,hashlib,json,struct
from decimal import Decimal
from pathlib import Path


def main():
    R=Path(__file__).resolve().parents[1];N=R/'work/rr_migration_remaining_tail_integration_20261016/native_pair'
    manifest=N/'manifest.json';protocol=N/'protocol.json';p=json.loads(protocol.read_text());state=json.loads(manifest.read_text())
    assert state['status']=='ten_three_layer_native_migration_runs_terminal_requires_independent_review'
    assert len(state['runs'])==10 and len(state['steps'])==60
    assert all(s['status']=='terminal' and s['returncode']==0 for s in state['steps'])
    assert sum(s['wall_ns'] for s in state['steps'])<=sum(r['wall_ns'] for r in state['runs'])<=state['wall_ns']
    refs={}
    def sha(path):
        path=Path(path);key=str(path.resolve())
        if key not in refs:
            h=hashlib.sha256()
            with path.open('rb') as stream:
                for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
            refs[key]=h.hexdigest()
        return refs[key]
    for path,h in p['source_sha256'].items():assert sha(path)==h,path
    diesfile=Path(p['topology_prefix']+'.node_die');dies=[r[0] for r in struct.iter_unpack('<H',diesfile.read_bytes())]
    baseline=R/'work/native_joint_budget_net_repair_v2_20261016/protocol.json';case=json.loads(baseline.read_text())['cases'][0]
    def crossings(path):
        seen=set();total=0
        for r in csv.DictReader(Path(path).open()):
            net,u,v=(int(r[k]) for k in ['net_id','parent','child']);assert (net,v) not in seen;seen.add((net,v));total+=dies[u]!=dies[v]
        return total
    baseline_cross=crossings(case['native_tree']);outcomes={}
    for arm in ['static','adaptive']:
        runs=sorted([r for r in state['runs'] if r['arm']==arm],key=lambda r:r['repeat']);assert [r['repeat'] for r in runs]==list(range(5))
        previous=None;qualities=[]
        for run in runs:
            D=Path(run['directory']);qfile=D/'native_validation/validation.json';q=json.loads(qfile.read_text());assert q==run['quality'] and q['legal']
            assert sha(D/'native.route')==q['inputs']['route_sha256']
            assert sha(Path(p['timing_build'])/'build/vpr/vpr')==q['inputs']['vpr_sha256']
            actual=json.loads((D/'route.json').read_text());assert actual==run['counters'] and actual['remaining_layer_tail'] and actual['task_placement_mode']==p['arms'][arm]['placement']
            for filename in ['resource_seed_replay.json','credit_replay.json','tree_audit.json','session_provenance_audit.json']:
                proofpath=D/filename;proof=json.loads(proofpath.read_text());sha(proofpath)
                assert proof.get('status'),filename
                for path,h in proof.get('source_sha256',{}).items():assert sha(path)==h,path
            credit=json.loads((D/'credit_replay.json').read_text());assert credit['final_credits_empty']
            actual.pop('wall_ms');hashes={f.name:sha(f) for f in D.glob('route.*') if f.name!='route.json'}
            if previous is not None:assert previous==(actual,hashes),(arm,run['repeat'])
            previous=(actual,hashes)
            cross=crossings(D/'route.route_trees.csv')
            passed=(q['total_wirelength']<=case['baseline_wirelength'] and Decimal(str(q['critical_path_delay_ns']))<=Decimal(str(case['baseline_cpd_ns'])) and cross<=baseline_cross)
            qualities.append(dict(repeat=run['repeat'],wirelength=q['total_wirelength'],cpd_ns=q['critical_path_delay_ns'],crossings=cross,joint_baseline_pass=passed,full_run_wall_ns=run['wall_ns'],backpressure=credit['events'].get('backpressure',0),transfers=credit['tickets'],fallbacks=actual['fallbacks'],remote_shadow_reads=actual['remote_shadow_reads']))
            sha(qfile);sha(D/'route.json')
        outcomes[arm]=qualities
    for f in [manifest,protocol,diesfile,baseline,Path(case['native_tree']),Path(__file__)]:sha(f)
    O=R/'work/three_layer_migration_native_pair_review_20261016';O.mkdir(exist_ok=False)
    report=dict(status='ten_same_graph_migration_runs_integrity_repeat_and_native_quality_reviewed',outcomes=outcomes,source_sha256=refs,research_complete=False,adopted=False,scope='Five same-configuration repeats per arm. Per-run native quality and crossing comparisons; frozen producer pressure/seed/resource/credit/tree/provenance proof integrity checked, not independently re-solved search. Full run times include explicitly timed verification. Neither proxy counts nor emulation imply physical throughput/energy. Postprocessing refinement not run in these paired results.')
    (O/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(outcomes))


if __name__=='__main__':main()
