"""All9 predeclared source-input arm/case models; original local feedback guards."""
import contextlib,json,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from compact_persistent_native_model_session_v1 import Session
from compiled_criticality_tree_v1 import Graph,BINARY
from run_native_endpoint_source_context_feedback_v1_2026_10_18 import predict

def main():
 total=time.perf_counter();E=R/'experiments';out=E/'mmc_source_context_ablation_v1_2026-10-18';out.mkdir(exist_ok=False);(out/'logs').mkdir();sp=E/'mmc_source_context_input_ablation_protocol_v1_2026-10-18/protocol.json';spec=json.loads(sp.read_text());assert all(sha(k)==h for k,h in spec['bindings'].items());corep=E/'source_context_feedback_fork_contract_v1_2026-10-18/verification.json';core=json.loads(corep.read_text());assert core['original_algorithm_and_all_admission_bodies_unchanged'] and all(sha(k)==h for k,h in core['bindings'].items());ip=E/'mmc_source_context_inputs_v1_2026-10-18/independent_verification_v1.json';iv=json.loads(ip.read_text());assert iv['status']=='all3_source_context_input_payloads_independently_verified' and all(sha(k)==h for k,h in iv['bindings'].items());bindings={**closure([Path(__file__)]),str(BINARY):sha(BINARY),str(sp):sha(sp),str(corep):sha(corep),str(ip):sha(ip)};arms=list(spec['arms']);assert len(arms)==3;(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=['case_01','case_02','case_03'],arms=arms,primary_candidate=spec['primary_candidate'],source_input_staging_receipt=str(ip.parent/'receipt.json'),scope='Source data ablation only; old warm paths/floors/budgets and original2round local scheduling/admission retained. All9 final-frame/event and original cold quality audits required.'),indent=2));endpoint=E/'mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';tick=time.perf_counter();graph,digest,nodes,fields,rc,_=load_endpoints(endpoint);shared=time.perf_counter()-tick;print('SOURCE_CONTEXT_SHARED_GRAPH_READY',shared,flush=True);rows=[]
 for case in ['case_01','case_02','case_03']:
  folder=out/case;folder.mkdir();endpoint=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';ep=json.loads(endpoint.read_text());warm=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained';oldp=json.loads((warm.parent/'feedback_on/native_retained/protocol.json').read_text())
  for arm in arms:
   s=object.__new__(Session);s.closed=False;s.active=False;s.owner=None;s.base=None;s.graph=graph;s.digest=digest;s.nodes=nodes;s.fields=fields;s.rc=rc;s.sources=bindings.copy();s.net_digest=ep['inputs']['net']['sha256'];s.net_names=ep['net_names'];s.identities={q['connection_id']:q['net_id'] for q in ep['connections']};s.current_queries=None;s.binds=0;tick=time.perf_counter();s.search=Graph(fields,rc.increments,[rc.initial(n) for n in range(len(nodes))]);workspace=time.perf_counter()-tick;print('SOURCE_CONTEXT_MODEL_START',case,arm,flush=True)
   try:
    with (out/'logs'/f'{case}_{arm}.log').open('x') as log,contextlib.redirect_stdout(log):result=predict(endpoint,folder/arm,oldp['structural_node_base_proof'],Path(oldp['criticality_input_proof']).parent,warm,'local',session=s,source_context_directory=E/f'mmc_source_context_inputs_v1_2026-10-18/{case}',source_context_arm=arm)
    assert sha(folder/arm/'initial.json')==sha(warm/'initial.json');receipt=json.loads((folder/arm/'receipt.json').read_text());row=dict(case=case,arm=arm,result=result,compiled_workspace_setup_seconds=workspace,rounds=[dict(round_index=r['round_index'],NETs=len(r['events']),overflow_before=r['overflow_before'],overflow_after=r['overflow_after'],commits=sum(e['status']=='COMMITTED' for e in r['events'])) for r in receipt['rounds']]);rows.append(row);print('SOURCE_CONTEXT_MODEL_DONE',json.dumps(row),flush=True)
   except Exception:(out/f'{case}_{arm}_failure.txt').write_text(traceback.format_exc());raise
   finally:s.close()
 assert len(rows)==9 and all(sha(k)==h for k,h in bindings.items());(out/'results.json').write_text(json.dumps(dict(status='all9_source_input_ablation_models_complete_audits_pending',bindings=bindings,shared_graph_setup_seconds=shared,cases=rows,producer_elapsed_before_final_summary_seconds=time.perf_counter()-total),indent=2))
if __name__=='__main__':main()
