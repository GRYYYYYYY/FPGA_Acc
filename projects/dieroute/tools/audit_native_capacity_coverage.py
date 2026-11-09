"""Verify all preregistered native baselines, retaining failed attempts explicitly."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'work/native_capacity_coverage_20261017'

def main():
    hashes={}
    def sha(p):
        p=Path(p).resolve()
        if str(p) not in hashes:
            h=hashlib.sha256()
            with p.open('rb') as f:
                for b in iter(lambda:f.read(1048576),b''):h.update(b)
            hashes[str(p)]=h.hexdigest()
        return hashes[str(p)]
    def load(p):return json.loads(Path(p).read_text())
    p=load(D/'protocol.json'); launch=load(D/'launch_protocol.json')
    for protocol in [p,launch]:
        for f,h in protocol['inputs'].items():assert sha(f)==h,f
    result=load(D/'result.json');assert result['status']=='six_capacity_scaling_native_baseline_attempts_terminal'
    assert len(result['cases'])==len(p['commands'])==6
    declared=load(R/'experiments/native_capacity_coverage_protocol_20261017.json')
    assert sha(D/'protocol.json')==declared['protocol_sha256']
    assert [(v['width'],v['height'],v['case'],v['seed']) for v in p['commands']]==[(w,h,c,seed) for w,h in declared['geometries'] for c in declared['cases'] for seed in declared['seeds']]
    original=(R/'work/reserved_native_baselines_20261017/architecture.xml').read_text()
    for width,height in declared['geometries']:
        arch=D/f'architecture_{width}x{height}.xml'
        expected,count=re.subn(r'<fixed_layout name="DieRouteSBScale3" width="13" height="10">',f'<fixed_layout name="DieRouteCapacity{width}x{height}" width="{width}" height="{height}">',original)
        assert count==1 and arch.read_text()==expected
    rows=[]
    for recipe,entry in zip(p['commands'],result['cases']):
        assert recipe['label']==entry['case']
        directory=D/recipe['label'];run=load(directory/'run.json')
        assert run==entry['run'] and run['returncode']==entry['returncode']
        expected=[recipe['command'][recipe['command'].index('--vpr')+1],'architecture.xml','circuit.blif','--device',f"DieRouteCapacity{recipe['width']}x{recipe['height']}",'--route_chan_width','80','--seed',str(recipe['seed']),'--num_workers','1','--write_rr_graph','rr_graph.xml']
        assert run['command']==expected and Path(run['cwd'])==directory
        for v in run['sources'].values():assert sha(v['path'])==v['sha256']
        assert sha(directory/'architecture.xml')==sha(D/f"architecture_{recipe['width']}x{recipe['height']}.xml")
        assert sha(directory/'circuit.blif')==sha(D/(recipe['case']+'.blif'))
        for name,v in run['artifacts'].items():
            f=directory/name;assert f.stat().st_size==v['bytes'] and sha(f)==v['sha256'],f
        text=(directory/'vpr_stdout.log').read_text() if (directory/'vpr_stdout.log').exists() else (directory/'vpr.log').read_text()
        row=dict(case=recipe['case'],width=recipe['width'],height=recipe['height'],seed=recipe['seed'],returncode=run['returncode'],native_legal=False,elapsed_ns=run['elapsed_ns'])
        if run['returncode']==0:
            assert run['status']=='passed'
            for marker in ['Completed routing consistency check successfully.','Circuit successfully routed with a channel width factor of 80.','VPR succeeded']:assert marker in text,marker
            row.update(native_legal=True,wirelength=int(re.findall(r'Total wirelength:\s+(\d+)',text)[-1]),cpd_ns=float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)[-1]),graph_sha256=sha(directory/'rr_graph.xml'))
        else:
            assert run['status']=='failed'
            row['failure_log_tail']=text[-3000:]
            capacity=re.findall(r'Failed to find device which satisfies resource requirements[^\n]*',text)
            row['failure_class']=('packing_device_capacity' if capacity else 'routing_unroutable_at_fixed_width' if 'Circuit is unroutable with a channel width factor of 80.' in text else 'native_failure_requires_review')
            row['capacity_failure_messages']=capacity
        rows.append(row)
    for f in [D/'result.json',D/'manifest.json',D/'protocol.json',D/'launch_protocol.json',Path(__file__)]:sha(f)
    report=dict(status='six_capacity_scaling_baseline_integrity_geometry_and_native_outcomes_reviewed',outcomes=rows,source_sha256=hashes,scope='Native baseline integrity and printed routing consistency/QoR only; failed attempts retained without quality values. Six predeclared dimension/case attempts, one seed, capacity characterization after prior reserved inputs were opened. Not independent heldout evidence, candidate benefit or physical performance.',research_complete=False,board_result=False)
    with (D/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(dict(status=report['status'],legal=sum(x['native_legal'] for x in rows),attempts=len(rows))))

if __name__=='__main__':main()
