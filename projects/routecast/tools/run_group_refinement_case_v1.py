"""Fixed full off/on pair schedule with complete event admission after each arm."""
import json,sys,subprocess,hashlib,time,shutil
from pathlib import Path
from types import SimpleNamespace
from array import array
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from sequential_group_refinement_v1 import refine
E=R/'experiments';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';S=E/'prospective_external_family_blocker_root_pair_schedule_v2_2026-10-20';D=E/'prospective_external_family_sequential_group_refinement_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def execute(c,protocol,destination,schedule_directory):
 assert all(sha(k)==h for k,h in protocol['bindings'].items());case=c['case'];baseline=A/case/'native_retained/warm_timing_round_updated';source=read(baseline/'round1.json');source_sketch=read(baseline/'sketch.json');graph,digest,nodes,f,rc,queries=load_endpoints(c['endpoint']);slots={eid:i for i,eid in enumerate(f['edge_ids'])};original=SimpleNamespace(n=len(f['capacities']),offsets=f['row_offsets'],dest=f['dest_ranks'],inc=rc.increments,initial=tuple(rc.initial(i) for i in range(len(f['capacities']))),repair_bounds=None);basefile=Path(c['node_base_proof']).parent/'node_base.u64';base=array('Q');base.frombytes(basefile.read_bytes());base=tuple(base);spans={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in ('CHANX','CHANY')};criticalities={q['connection_id']:q for q in read(baseline/'timing_round1.json')['criticalities']};schedule=read(schedule_directory/case/'schedule.json');bindings=dict(protocol['bindings'])
 for p in [baseline/'round1.json',baseline/'sketch.json',baseline/'complete_event_audit.json',baseline/'timing_round1.json',schedule_directory/case/'schedule.json',basefile,Path(c['endpoint'])]:bindings[str(p)]=sha(p)
 for enabled,arm in [(False,'off'),(True,'on')]:
  out=destination/case/arm;start=time.perf_counter();final,summary=refine(f,rc,slots,original,queries,criticalities,base,spans,source,schedule,out,enabled,10000)
  if not enabled:
   assert final==source;shutil.copyfile(baseline/'sketch.json',out/'sketch.json')
  else:
   independent=Counter()
   for q in final['records']:independent.update({q['source']}|{f['dest_ranks'][slots[eid]] for eid in q['answer']['physical_edge_ids']})
   ledger={int(n):v for n,v in final['ledger'].items()};sketch=dict(source_sketch,records=final['records'],ledger=final['ledger'],epochs=final['epochs'],independent_connection_ledger=dict(independent),overflow_units=sum(max(0,v-f['capacities'][n]) for n,v in ledger.items()),overflow_nodes=sum(v>f['capacities'][n] for n,v in ledger.items()));assert not sketch['eligible_for_legal_route_commit'];(out/'sketch.json').write_text(json.dumps(sketch)+'\n')
  (out/'protocol.json').write_text(json.dumps(dict(case=case,enabled=enabled,bindings=bindings,baseline=str(baseline),endpoint=c['endpoint'],schedule=str(schedule_directory/case/'schedule.json'),node_base_proof=c['node_base_proof'],max_labels_per_query=10000,checkpoint_interval=256,policy=protocol['policy']),indent=2)+'\n');assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(status='REFINEMENT_ARM_GENERATED_AUDIT_PENDING',component_seconds=time.perf_counter()-start,summary=summary,bindings=bindings,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n')
  subprocess.run([sys.executable,str(R/'tools/verify_sequential_group_refinement_v1.py'),str(out),str(out/'complete_event_audit.json')],cwd=R,check=True);print('ARM_AUDITED',case,arm,summary['counts'],flush=True)
def main():
 protocol=read(D/'protocol.json');c=next(q for q in protocol['cases'] if q['case']==sys.argv[1]);execute(c,protocol,D,S)
if __name__=='__main__':main()
