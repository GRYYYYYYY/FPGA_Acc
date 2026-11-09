"""Frozen owner-expanded scheduling, three exposed layouts; no gate relaxation."""
import contextlib,json,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from compact_persistent_native_model_session_v1 import Session
from compiled_criticality_tree_v1 import Graph,BINARY
from run_native_endpoint_owner_feedback_v1_2026_10_18 import predict

def main():
 E=R/'experiments';out=E/'mmc_owner_expansion_feedback_v1_2026-10-18';out.mkdir(exist_ok=False);(out/'logs').mkdir()
 specp=E/'mmc_owner_expansion_candidate_protocol_v1_2026-10-18/protocol.json';corep=E/'overuse_owner_schedule_core_v1_2026-10-18/verification.json'
 for p in [specp,corep]:
  doc=json.loads(p.read_text());assert all(sha(k)==v for k,v in doc['bindings'].items())
 bindings={**closure([Path(__file__)]),str(BINARY):sha(BINARY),str(specp):sha(specp),str(corep):sha(corep)}
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=['case_01','case_02','case_03'],scope='Development only; original two rounds, initialization and acceptance guards. Frame/event and original cold quality audits pending.'),indent=2))
 tick=time.perf_counter();endpoint=E/'mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';graph,digest,nodes,fields,rc,_=load_endpoints(endpoint);setup=time.perf_counter()-tick;rows=[]
 print('SHARED_GRAPH_LOADED',setup,flush=True)
 for case in ['case_01','case_02','case_03']:
  endpoint=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';metadata=json.loads(endpoint.read_text());warm=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained';oldp=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/feedback_on/native_retained/protocol.json';p=json.loads(oldp.read_text())
  s=object.__new__(Session);s.closed=False;s.active=False;s.owner=None;s.base=None;s.graph=graph;s.digest=digest;s.nodes=nodes;s.fields=fields;s.rc=rc;s.sources=bindings.copy();s.net_digest=metadata['inputs']['net']['sha256'];s.net_names=metadata['net_names'];s.identities={q['connection_id']:q['net_id'] for q in metadata['connections']};s.current_queries=None;s.binds=0
  tick=time.perf_counter();s.search=Graph(fields,rc.increments,[rc.initial(n) for n in range(len(nodes))]);workspace=time.perf_counter()-tick
  print('CASE_START',case,flush=True)
  try:
   with (out/'logs'/f'{case}.log').open('x') as log,contextlib.redirect_stdout(log):
    result=predict(endpoint,out/case,p['structural_node_base_proof'],Path(p['criticality_input_proof']).parent,warm,'overuse_owners',session=s)
   assert sha(out/case/'initial.json')==sha(warm/'initial.json')
   receipt=json.loads((out/case/'receipt.json').read_text());row=dict(case=case,result=result,compiled_workspace_setup_seconds=workspace,rounds=[{k:r[k] for k in ['round_index','overflow_before','overflow_after']}|dict(affected_nets=len(r['affected_nets']),commits=sum(e['status']=='COMMITTED' for e in r['events'])) for r in receipt['rounds']]);rows.append(row);print('CASE_DONE',json.dumps(row),flush=True)
  except Exception:
   (out/f'{case}_failure.txt').write_text(traceback.format_exc());raise
  finally:s.close()
 assert all(sha(k)==v for k,v in bindings.items())
 (out/'results.json').write_text(json.dumps(dict(status='all3_candidate_feedback_complete_audits_pending',bindings=bindings,shared_graph_setup_seconds=setup,cases=rows),indent=2))
if __name__=='__main__':main()
