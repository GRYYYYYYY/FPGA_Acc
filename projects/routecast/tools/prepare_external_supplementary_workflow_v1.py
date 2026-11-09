"""Freeze fixed development commands, dependencies, artifacts and timing limits."""
import json,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent/'native_resume_prototype')]
from source_binding_v2 import closure
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];T=R/'tools';O=R/'experiments/prospective_external_family_supplementary_development_v1_2026-10-19'
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def main():
    O.mkdir(exist_ok=False);bundle_path=R/'experiments/prospective_external_family_all_frame_input_bundle_v2_2026-10-19/verification.json';bundle=json.loads(bundle_path.read_text());inputs={r['case']:r for r in bundle['rows']}
    np=R/'experiments/prospective_external_family_native_case_manifest_v1_2026-10-19/manifest.json';native=json.loads(np.read_text());up=R/'experiments/prospective_external_family_native_utility_manifest_v2_2026-10-19/manifest.json';utility=json.loads(up.read_text())
    native['full_workflow_admitted']=True;utility['full_workflow_admitted']=True
    diagnostic=R/'experiments/prospective_external_family_termination_diagnostic_v1_2026-10-19/manifest.json';archive=json.loads(diagnostic.read_text());archives={r['width']:r for r in archive['cases'] if r['termination_policy']=='disable_early_abort_max300'}
    for collection in (native,utility):
        collection['bindings'][str(diagnostic)]=sha(diagnostic)
        collection['bindings'][str(diagnostic.parent/'research_decision_v1.json')]=sha(diagnostic.parent/'research_decision_v1.json')
        for row in collection['cases']:
            row['command'][row['command'].index('--max_router_iterations')+1]='300'
            row['command']+=['--routing_failure_predictor','off','--router_init_wirelength_abort_threshold','1000000000']

    for row in native['cases']:row['output']=archives[row['width']]['output'] if row['frame']=='source' else str(O/'native'/row['case'])
    for row in utility['cases']:
        row['output']=str(O/'utility'/row['case']);row['preload_directory']=str(O/'preloads'/row['target_case'])
    native_file=O/'native_manifest.json';utility_file=O/'utility_manifest.json';write(native_file,native);write(utility_file,utility)
    stages=[];scripts=set();specfiles=[];target_cases=[];source_cases=[];comparison_rows=[]
    def stage(id,script,args,deps,artifacts,parents=(),requirements=None,always=False):
        script=T/script;scripts.add(script)
        stages.append(dict(id=id,argv=[sys.executable,str(script),*map(str,args)],depends_on=deps,artifacts=list(map(str,artifacts)),create_parents=list(map(str,parents)),required_json={str(p):v for p,v in (requirements or {}).items()},always_run=always))
    native_rows={r['case']:r for r in native['cases']}
    for width in (96,128,160):
        w=f'w{width:03d}';src_case=w+'/source';source_cases.append(src_case);src=inputs[src_case];n=native_rows[src_case];src_native=Path(n['output']);checkpoint=O/'source_checkpoints'/w
        sid='native/'+src_case;stage(sid,'admit_external_archived_native_source_v1.py',[diagnostic,archives[width]['case']],[],[src_native/'verification.json'],requirements={src_native/'verification.json':{'status':'FULL_PHYSICAL_AND_CANONICAL_PASS'}})
        iid='source_import/'+w;stage(iid,'prepare_external_native_source_checkpoint_v1.py',[src['endpoint'],src_native/'output.route',src['floor_proof'],checkpoint],[sid],[checkpoint/'receipt.json'],[checkpoint.parent])
        aid='source_audit/'+w;stage(aid,'verify_external_native_source_checkpoint_xml_v1.py',[checkpoint],[iid],[checkpoint/'independent_xml_verification_v1.json'])
        for episode in (1,2,3):
            case=w+f'/episode_{episode:02d}';target_cases.append(case);row=inputs[case];case_dir=O/'predictions'/case;warm=case_dir/'warm'
            wid='warm/'+case;stage(wid,'prepare_external_warm_initializers_v1.py',[row['endpoint'],checkpoint,row['floor_proof'],warm],[aid],[warm/'raw_min/receipt.json',warm/'native_retained/receipt.json'],[case_dir])
            audit_ids=[];pred={}
            for init,method in [('raw_min','raw_min_on'),('native_retained','native_retained_on')]:
                warm_audit='warm_audit/'+case+'/'+init;stage(warm_audit,'verify_external_warm_initializers_xml_v1.py',[warm/init],[wid],[warm/init/'verification.json'])
                pred_dir=case_dir/method;pid='predict/'+case+'/'+method;stage(pid,'run_external_native_timing_feedback_v2_2026_10_19.py',[row['endpoint'],pred_dir,row['node_base_proof'],row['criticality_directory'],warm/init,'all'],[warm_audit],[pred_dir/'receipt.json',pred_dir/'sketch.json'])
                full_audit='event_audit/'+case+'/'+method;proof=pred_dir/'complete_event_audit.json';stage(full_audit,'verify_external_current_timing_feedback_events_v1.py',[pred_dir,case+'_'+method,proof],[pid],[proof]);audit_ids.append(full_audit);pred[method]=dict(frame=str(pred_dir/'sketch.json'),proof=str(proof))
            target_native=Path(native_rows[case]['output']);nid='native/'+case;stage(nid,'run_external_native_route_case_v1.py',[native_file,case],[aid],[target_native/'verification.json'],requirements={target_native/'verification.json':{'status':'FULL_PHYSICAL_AND_CANONICAL_PASS'}})
            domain=R/f'experiments/prospective_external_family_quality_domains_v2_2026-10-19/{w}/verification.json';domain_ind=domain.parent.parent/'independent_verification_v1.json'
            spec=O/'specifications'/case/'comparison_spec.json';write(spec,dict(schema='ROUTECAST_EXTERNAL_FORECAST_CASE_V1',case=case,endpoint=row['endpoint'],domain_proof=str(domain),domain_independent_proof=str(domain_ind),source_proof=str(checkpoint/'independent_xml_verification_v1.json'),source_frame=str(checkpoint/'initial.json'),predictions=pred,label_proof=str(target_native/'verification.json'),label_physical_audit=str(target_native/'physical_audit.json')));specfiles.append(spec)
            comparison=case_dir/'comparison.json';stage('compare/'+case,'evaluate_external_forecast_case_v1.py',[spec,comparison],[*audit_ids,nid],[comparison]);comparison_rows.append(dict(case=case,comparison=str(comparison)))
            preload=O/'preloads'/case;export_id='export/'+case;stage(export_id,'export_external_excess_preload_v1.py',[pred['native_retained_on']['frame'],pred['native_retained_on']['proof'],domain,preload],[audit_ids[1]],[preload/'verification.json'],[preload.parent])
            for arm in ('disabled','zero','forecast'):
                job=next(r for r in utility['cases'] if r['target_case']==case and r['utility_arm']==arm);out=Path(job['output'])
                stage('utility/'+case+'/'+arm,'run_external_native_excess_utility_case_v2.py',[utility_file,job['case']],[export_id],[out/'verification.json'],requirements={out/'verification.json':{'status':'FULL_PHYSICAL_AND_CANONICAL_PASS','independent_trace_replay_pass':True}})
    cohort_spec=O/'specifications/forecast_cohort.json';write(cohort_spec,dict(cases=comparison_rows));specfiles.append(cohort_spec)
    stage('summary/forecast','summarize_external_forecast_cohort_v1.py',[cohort_spec,O/'forecast_comparison.json'],[s['id'] for s in stages if s['id'].startswith('compare/')],[O/'forecast_comparison.json'],always=True)
    stage('summary/utility','summarize_external_native_utility_v1.py',[utility_file,O/'utility_comparison.json'],[s['id'] for s in stages if s['id'].startswith('utility/')],[O/'utility_comparison.json'],always=True)
    runner=T/'run_external_development_workflow_v1.py';scripts.update([Path(__file__).resolve(),runner]);bindings={**native['bindings'],**utility['bindings'],**closure(list(scripts))}
    for p in [bundle_path,np,up,diagnostic,diagnostic.parent/'research_decision_v1.json',native_file,utility_file,*specfiles]:bindings[str(p)]=sha(p)
    for row in bundle['rows']:
        for path,h in row['bindings'].items():bindings[path]=h
    if not all(sha(p)==h for p,h in bindings.items()):raise ValueError('dependency changed before freeze')
    timing='Continuous serial stage clocks include child startup/staging/search/import/audit/export/native/canonical and interstage bookkeeping to before final terminal serialization. Individual clocks exclude following ledger serialization; continuous clock includes prior ledgers. Historical synthesis/place/graph/timing/floor/price/caches/input admission costs remain paid dependencies; incomplete upstream total means full gain unproven. Utility disabled/zero/forecast process clocks diagnostic only; no balanced repeated complete-flow timing or hardware claim.'
    plan=dict(supplementary_only=True,primary_cohort_replaced=False,source_policy='Reuse all3 archived noearly300 outcomes; 96/128 unavailable retained, 160 source reusable only after FULL/physical/canonical reauthentication. All9 targets kept; no subset promotion.',schema='ROUTECAST_EXTERNAL_EXECUTABLE_DEVELOPMENT_WORKFLOW_V1',bindings=bindings,cwd=str(R),execution_directory=str(O/'execution'),source_cases=source_cases,target_cases=target_cases,stages=stages,timing_policy=timing,upstream_preparation_cost_complete=False,complete_workflow_gain_proven=False,strict_unseen_admitted=False,failure_policy='No retries/replacement/label-driven tuning. All nine target cases remain; failed dependency blocks dependents while other fixed cases continue. Final summaries run even with missing results.',scope='Executable fixed development forecast and native utility component workflow; full research objective and complete matched time gain remain open.')
    write(O/'workflow.json',plan);print('WORKFLOW_FROZEN',len(stages),O/'workflow.json')
if __name__=='__main__':main()
