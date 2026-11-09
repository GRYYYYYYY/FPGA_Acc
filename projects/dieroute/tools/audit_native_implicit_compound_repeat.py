"""Read-only terminal review through isolated audit views of repeated stage outputs."""
import hashlib,json,subprocess,sys
from pathlib import Path
import audit_compound_repeat_sweep_stage as sweep_audit
import audit_compound_repeat_refresh_stage as refresh_audit

R=Path(__file__).resolve().parents[1]
D=R/'work/native_implicit_compound_repeat_v2_20261017'
O=R/'work/native_implicit_compound_review_20261017'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def loadtree(path):
    import csv
    result={}
    for row in csv.DictReader(Path(path).open()):
        key=(int(row['net_id']),int(row['child']));value=(int(row['source']),int(row['parent']))
        assert key not in result;result[key]=value
    return result

def main():
    state=json.loads((D/'manifest.json').read_text())
    assert state['status']=='three_case_compound_repeat_terminal_requires_independent_review'
    assert len(state['cases'])==3 and len(state['stages'])==21
    assert all(s['status']=='terminal' and s.get('returncode',0)==0 and s['wall_ns']>=0 for s in state['stages'])
    O.mkdir(exist_ok=False)
    root_protocol=json.loads((D/'protocol.json').read_text());refs={}
    for p,h in root_protocol['source_sha256'].items():assert sha(p)==h,p
    views=[]
    for name,module,source in [('sweep',sweep_audit,'native_joint_budget_net_repair_v2_20261016'),('refresh',refresh_audit,'native_refreshed_critical_policy_v1_20261016')]:
        view=O/name;view.mkdir();original=R/'work'/source
        protocol=json.loads((original/'protocol.json').read_text())
        if name=='refresh':
            for c in protocol['cases']:
                c['policy_parent_tree']=json.loads((D/'sweep'/c['label']/'manifest.json').read_text())['current_tree']
        (view/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
        if name=='sweep':(view/'launch_protocol.json').symlink_to(original/'launch_protocol.json')
        (view/'manifest.json').write_text(json.dumps(dict(status='three_case_single_sweeps_complete_requires_independent_review'))+'\n')
        for c in protocol['cases']:(view/c['label']).symlink_to(D/name/c['label'],target_is_directory=True)
        module.P=view;module.main();views.append(view/'independent_audit.json')
    comparisons=[]
    for c in state['cases']:
        label=c['case'];previous=R/'work/native_refreshed_critical_policy_v1_20261016'/label/'manifest.json';old=json.loads(previous.read_text())
        same=loadtree(c['final_tree'])==loadtree(old['current_tree'])
        oldq=old['current_quality'];q=c['quality']
        quality_same=all(q[k]==oldq[k] for k in ['total_wirelength','critical_path_delay_ns']) and c['crossings']==old['final_crossings']
        decision_equality={}
        for stage in ['sweep','refresh']:
            prior=json.loads((R/'work/native_instrumented_compound_repeat_20261016'/stage/label/'manifest.json').read_text())
            current=json.loads((D/stage/label/'manifest.json').read_text())
            def decisions(state):
                return [{k:v for k,v in step.items() if k not in ['wall_ns','native_evidence','validation']} for step in state['steps']]
            decision_equality[stage]=decisions(prior)==decisions(current)
        comparisons.append(dict(case=label,final_tree_identical=same,quality_identical=quality_same,decisions_identical=decision_equality,full_case_wall_ns=c['wall_ns']))
        refs[str(previous)]=sha(previous)
    for p in [D/'manifest.json',D/'protocol.json',*views,Path(__file__)]:refs[str(p)]=sha(p)
    output=dict(status='implicit_compound_stage_replays_trees_quality_and_decisions_compared',comparisons=comparisons,total_run_wall_ns=state['wall_ns'],source_sha256=refs,research_complete=False,adopted=False,scope='Implicit-CSR implementation substituted with unchanged configuration; native decision replay and exact comparison of search counters, selections, budgets, acceptance and final routes. CPU full-run timing only; concurrent background work prevents attributing all wall differences solely to this change. Wall time includes explicitly labeled verification stages; preflight source hashing excluded. Not a new seed, heldout, FPGA or physical-card result.')
    (O/'independent_audit.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps(comparisons))

if __name__=='__main__':main()
