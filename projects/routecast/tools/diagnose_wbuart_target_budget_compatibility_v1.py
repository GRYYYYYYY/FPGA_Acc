"""Posthoc native target path versus unchanged heuristic budgets, all9 cases."""
import json,hashlib,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
E=R/'experiments';N=E/'wbuart_native_evaluation_v1_2026-10-20';D=E/'wbuart_native_target_budget_diagnosis_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);workflow=read(N/'workflow.json');bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/load_complete_route_state_v1.py',R/'tools/compact_stream_rc_endpoint_context_v1.py',N/'workflow.json']};rows=[]
 for c in workflow['comparisons']:
  spec=read(c['specification']);ep=Path(spec['endpoint']);meta=read(ep);label=read(spec['label_proof']);assert label['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS'
  for n,h in label['bindings'].items():assert sha(n)==h
  source=read(spec['source_frame']);prior={q['connection_id']:q for q in source['records']};warmdir=E/'wbuart_warm_inputs_v1_2026-10-20'/c['case']/'native_retained';warmproof=read(warmdir/'verification.json');assert warmproof['native_staged_state_independent_xml_pass']
  for n,h in warmproof['bindings'].items():assert sha(n)==h
  warm=read(warmdir/'initial.json');budget={q['connection_id']:q for q in warm['records']};graph,digest,nodes,fields,rc,queries=load_endpoints(ep);route=Path(spec['label_physical_audit']).parent/'output.route';paths,native,ledger=load_complete(route,meta,nodes,fields,rc);delay={q['connection_id']:q['delay_integer'] for q in native};assert len(delay)==2493 and digest==warm['graph_sha256'] and rc.scale==10**18
  categories={};priority={'endpoint_unchanged':0,'sink_only':1,'source_moved':2}
  for q in queries:
   old=prior[q['connection_id']];cat='source_moved' if q['source']!=old['source'] else 'sink_only' if q['sink']!=old['sink'] else 'endpoint_unchanged';net=q['net_id']
   if priority[cat]>priority.get(categories.get(net),-1):categories[net]=cat
  output=[];per=defaultdict(Counter);badnets=defaultdict(set);violations=0
  for q in queries:
   cid=q['connection_id'];r=budget[cid];assert all(q[k]==r[k] for k in ['net_id','source','sink','full_connection_id']);value=delay[cid];floor=r['floor_integer'];limit=r['budget_integer'];assert floor<=value;bad=value>limit;excess=max(0,value-limit);cat=categories[q['net_id']];violations+=bad;per[cat]['connections']+=1;per[cat]['violations']+=bad;per[cat]['total_excess']+=excess
   if bad:badnets[cat].add(q['net_id'])
   output.append(dict(q,target_delay_integer=value,floor_integer=floor,budget_integer=limit,violation=bad,excess_integer=excess,category=cat))
  for cat in priority:per[cat]['NETs_with_violation']=len(badnets[cat])
  d=D/c['case'];d.mkdir(parents=True);payload=d/'connections.json';payload.write_text(json.dumps(output)+'\n');rows.append({'case':c['case'],'connections':2493,'violations':violations,'NETs_with_violation':len(set().union(*badnets.values())) if badnets else 0,'categories':{k:dict(per[k]) for k in priority},'payload':str(payload),'payload_sha256':sha(payload),'source_frame':spec['source_frame'],'endpoint':str(ep),'warm_directory':str(warmdir),'native_route':str(route)});print('WBUART_TARGET_BUDGET_DIAGNOSIS',c['case'],violations,flush=True)
  for p in [ep,route,Path(spec['source_frame']),warmdir/'initial.json',warmdir/'verification.json',payload,Path(spec['label_proof'])]:bindings[str(p)]=sha(p)
 assert len(rows)==9 and sum(r['connections'] for r in rows)==22437
 (D/'verification.json').write_text(json.dumps({'status':'ALL22437_NATIVE_TARGET_PATHS_COMPARED_WITH_FROZEN_CURRENT_BUDGETS','rows':rows,'connections':22437,'violations':sum(r['violations'] for r in rows),'budgets_labels_or_gates_changed':False,'new_route_search':False,'independent_fraction_parent_pointer_audit_pending':True,'scope':'Posthoc native solution compatibility, not proof every legal routing violates budgets or global infeasibility. No larger budgets or acceptance changes authorized by this diagnosis.','bindings':bindings},indent=2)+'\n')
if __name__=='__main__':main()
