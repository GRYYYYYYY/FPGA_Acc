"""Uniform all-NET scheduling ablation; original predictor and all guards unchanged."""
import contextlib,json,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from compact_persistent_native_model_session_v1 import Session
from compiled_criticality_tree_v1 import Graph,BINARY
from run_objective_only_endpoint_feedback_v1_2026_10_18 import predict

def main():
 E=R/'experiments';out=E/'mmc_objective_only_all_NET_v1_2026-10-18';out.mkdir(exist_ok=False);(out/'logs').mkdir();sp=E/'mmc_objective_only_all_NET_protocol_v1_2026-10-18/protocol.json';spec=json.loads(sp.read_text());assert all(sha(k)==h for k,h in spec['bindings'].items());assert len(spec['coverage'])==3 and all(c['NETs']==55300 and c['all_existing_primary_duplicate_sink_contracts_compatible'] for c in spec['coverage']);bindings={**closure([Path(__file__)]),str(sp):sha(sp),str(BINARY):sha(BINARY)};(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,specification=str(sp),cases=['case_01','case_02','case_03'],scope='Objective-only admission ablation: intermediate positive overflow permitted; original hard budget and two rounds unchanged. Complete frame/event/source-quality audits required; no candidate native utility.'),indent=2));endpoint=E/'mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';tick=time.perf_counter();graph,digest,nodes,fields,rc,_=load_endpoints(endpoint);setup=time.perf_counter()-tick;print('ALL_NET_SHARED_GRAPH_READY',setup,flush=True);rows=[]
 for case in ['case_01','case_02','case_03']:
  endpoint=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';ep=json.loads(endpoint.read_text());warm=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained';p=json.loads((warm.parent/'feedback_on/native_retained/protocol.json').read_text());s=object.__new__(Session);s.closed=False;s.active=False;s.owner=None;s.base=None;s.graph=graph;s.digest=digest;s.nodes=nodes;s.fields=fields;s.rc=rc;s.sources=bindings.copy();s.net_digest=ep['inputs']['net']['sha256'];s.net_names=ep['net_names'];s.identities={q['connection_id']:q['net_id'] for q in ep['connections']};s.current_queries=None;s.binds=0;tick=time.perf_counter();s.search=Graph(fields,rc.increments,[rc.initial(n) for n in range(len(nodes))]);workspace=time.perf_counter()-tick;print('ALL_NET_CASE_START',case,flush=True)
  try:
   with (out/'logs'/f'{case}.log').open('x') as log,contextlib.redirect_stdout(log):result=predict(endpoint,out/case,p['structural_node_base_proof'],Path(p['criticality_input_proof']).parent,warm,'all',session=s)
   assert sha(out/case/'initial.json')==sha(warm/'initial.json');receipt=json.loads((out/case/'receipt.json').read_text());assert all(len(r['affected_nets'])==len(r['events'])==55300 for r in receipt['rounds']);row=dict(case=case,result=result,compiled_workspace_setup_seconds=workspace,rounds=[dict(round_index=r['round_index'],NETs=len(r['events']),overflow_before=r['overflow_before'],overflow_after=r['overflow_after'],commits=sum(e['status']=='COMMITTED' for e in r['events'])) for r in receipt['rounds']]);rows.append(row);print('ALL_NET_CASE_DONE',json.dumps(row),flush=True)
  except Exception:(out/f'{case}_failure.txt').write_text(traceback.format_exc());raise
  finally:s.close()
 assert all(sha(k)==h for k,h in bindings.items());(out/'results.json').write_text(json.dumps(dict(status='all3_global_schedule_feedback_complete_independent_audits_pending',bindings=bindings,shared_graph_setup_seconds=setup,cases=rows),indent=2))
if __name__=='__main__':main()
