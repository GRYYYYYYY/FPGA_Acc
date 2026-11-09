"""Three fixed cases, isolated present schedule, one shared immutable RR payload."""
import contextlib,json,sys,time,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from compact_persistent_native_model_session_v1 import Session
from compiled_criticality_tree_v1 import Graph,BINARY
from run_native_endpoint_restart_present_v1_2026_10_18 import predict
def main():
 total=time.perf_counter();E=R/'experiments';out=E/'mmc_restart_present_schedule_v1_2026-10-18';out.mkdir();(out/'logs').mkdir();sp=E/'mmc_restart_present_schedule_protocol_v1_2026-10-18/protocol.json';cp=E/'mmc_restart_present_context_contract_v1_2026-10-18/verification.json'
 for p in (sp,cp):
  d=json.loads(p.read_text());assert all(sha(k)==h for k,h in d['bindings'].items())
 bindings={**closure([Path(__file__)]),str(BINARY):sha(BINARY),str(sp):sha(sp),str(cp):sha(cp)}
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,primary='restart_present_0_then_half',cases=['case_01','case_02','case_03']),indent=2)+'\n')
 stat=Path('/proc/self/stat').read_text().split(') ',1)[1].split();(out/'live_process.json').write_text(json.dumps(dict(pid=os.getpid(),startticks=stat[19]))+'\n')
 endpoint=E/'mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';tick=time.perf_counter();graph,digest,nodes,fields,rc,_=load_endpoints(endpoint);shared=time.perf_counter()-tick;rows=[];print('RESTART_GRAPH_READY',shared,flush=True)
 for case in ['case_01','case_02','case_03']:
  endpoint=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';ep=json.loads(endpoint.read_text());warm=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained';old=json.loads((warm.parent/'feedback_on/native_retained/protocol.json').read_text());s=object.__new__(Session);s.closed=False;s.active=False;s.owner=None;s.base=None;s.graph=graph;s.digest=digest;s.nodes=nodes;s.fields=fields;s.rc=rc;s.sources=bindings.copy();s.net_digest=ep['inputs']['net']['sha256'];s.net_names=ep['net_names'];s.identities={q['connection_id']:q['net_id'] for q in ep['connections']};s.current_queries=None;s.binds=0;tick=time.perf_counter();s.search=Graph(fields,rc.increments,[rc.initial(n) for n in range(len(nodes))]);workspace=time.perf_counter()-tick
  try:
   with (out/'logs'/f'{case}.log').open('x') as log,contextlib.redirect_stdout(log):result=predict(endpoint,out/case,old['structural_node_base_proof'],Path(old['criticality_input_proof']).parent,warm,'local',session=s)
   assert sha(out/case/'initial.json')==sha(warm/'initial.json');receipt=json.loads((out/case/'receipt.json').read_text());row=dict(case=case,result=result,workspace_seconds=workspace,rounds=[dict(index=x['round_index'],overflow_before=x['overflow_before'],overflow_after=x['overflow_after'],events=len(x['events']),commits=sum(e['status']=='COMMITTED' for e in x['events'])) for x in receipt['rounds']]);rows.append(row);print('RESTART_CASE_DONE',json.dumps(row),flush=True)
  finally:s.close()
 (out/'results.json').write_text(json.dumps(dict(status='all3_models_complete_independent_audits_pending',bindings=bindings,shared_graph_seconds=shared,cases=rows,producer_elapsed_before_summary_seconds=time.perf_counter()-total),indent=2)+'\n')
if __name__=='__main__':main()
