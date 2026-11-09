"""All9 source/warm/round stages, original labels and exact physical owner ledgers."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import defaultdict,Counter
from fractions import Fraction
from external_forecast_metrics_v1 import vectors,metrics,gate
R=Path(__file__).resolve().parents[1];E=R/'experiments';N=E/'wbuart_native_evaluation_v1_2026-10-20';D=E/'wbuart_quality_stage_diagnosis_v1_2026-10-20'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=True);assert not (D/'verification.json').exists();workflow=read(N/'workflow.json');forecast=read(E/'wbuart_forecasts_v1_2026-10-20/verification.json');bindings={str(p):sha(p) for p in [Path(__file__),N/'research_decision_v1.json',N/'workflow.json',E/'wbuart_forecasts_v1_2026-10-20/verification.json']};admitted={};graphs={};results=[]
 def admit(path):
  path=Path(path).resolve()
  if str(path) in admitted:return admitted[str(path)]
  p=read(path)
  for n,h in p['bindings'].items():
   if n in bindings:assert bindings[n]==h
   else:assert sha(n)==h;bindings[n]=h
  bindings[str(path)]=sha(path);admitted[str(path)]=p;return p
 for c in workflow['comparisons']:
  spec=read(c['specification']);ep=read(spec['endpoint']);w=int(c['case'].split('/')[0][1:]);gpath=Path(ep['inputs']['graph']['path']);digest=ep['graph_sha256']
  if digest not in graphs:
   us=array('I');vs=array('I');caps=array('I');kinds=[];stack=[]
   for event,e in ET.iterparse(gpath,events=['start','end']):
    if event=='start':stack.append(e);continue
    parent=stack[-2].tag if len(stack)>1 else None
    if (e.tag,parent)==('node','rr_nodes'):assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'))
    elif (e.tag,parent)==('edge','rr_edges'):us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')))
    if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
    stack.pop()
   assert sha(gpath)==digest;graphs[digest]=(us,vs,caps,kinds)
  us,vs,caps,kinds=graphs[digest];domain=admit(spec['domain_proof']);admit(spec['domain_independent_proof']);label=admit(spec['label_proof']);truthpath=Path(spec['label_physical_audit']);assert label['bindings'][str(truthpath)]==sha(truthpath);truthdata=read(truthpath);assert truthdata['overflow_units']==0;folder=Path(spec['domain_proof']).parent;resources=[json.loads(s) for s in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');truth=vectors(resources,bins,{int(n):v for n,v in truthdata['node_occupancy'].items()},len(caps),truth=True);comparison=read(c['comparison']);arms=next(x['arms'] for x in forecast['rows'] if x['case']==c['case']);q={r['connection_id']:r for r in ep['connections']};stages=[];warmstates={}
  def add(name,path,proof,init=None,parent=None,expected=None):
   path=Path(path).resolve();p=admit(proof);assert p['bindings'].get(str(path))==sha(path);state=read(path);records=state['records'];assert len(records)==2493 and {r['connection_id'] for r in records}==set(q);owners=defaultdict(set);parents=defaultdict(dict)
   for r in records:
    cid=r['connection_id'];assert (r['net_id'],r['full_connection_id'])==(q[cid]['net_id'],q[cid]['full_connection_id']);u=r['source'];visited={u};assert kinds[u]=='SOURCE';owners[r['net_id']].add(u)
    for i,eid in enumerate(r['answer']['physical_edge_ids']):
     assert 0<=eid<len(us) and us[eid]==u;v=vs[eid];assert v not in visited and caps[v]>0
     if kinds[v]!='SINK':
      assert kinds[v]!='SOURCE';previous=parents[r['net_id']].get(v);assert previous is None or previous==(u,eid);parents[r['net_id']][v]=(u,eid)
     else:assert i==len(r['answer']['physical_edge_ids'])-1
     visited.add(v);owners[r['net_id']].add(v);u=v
    assert u==r['sink'] and kinds[u]=='SINK'
   ledger=Counter(n for support in owners.values() for n in support);assert dict(ledger)=={int(n):v for n,v in state['ledger'].items()};m=metrics(vectors(resources,bins,dict(ledger),len(caps)),truth,domain['resource_k'],domain['spatial_k']);small={s:{k:v for k,v in x.items() if k in ['spearman','top_k_hits','k','universe_size','mae']} for s,x in m.items()}
   if expected:
    for s in ['resource','spatial']:assert abs(m[s]['spearman']-expected[s]['spearman'])<=1e-12 and m[s]['top_k_hits']==expected[s]['top_k_hits']
   changed=[]
   if init:
    old=warmstates[init];changed=[r for r in records if (r['source'],r['answer']['physical_edge_ids'])!=(old[r['connection_id']]['source'],old[r['connection_id']]['answer']['physical_edge_ids'])]
   row={'stage':name,'frame':str(path),'proof':str(Path(proof).resolve()),'initializer':init,'parent':parent,'metrics':small,'overflow_units':sum(max(0,v-caps[n]) for n,v in ledger.items()),'changed_CIDs_from_warm':len(changed) if init else None,'changed_NETs_from_warm':len({r['net_id'] for r in changed}) if init else None,'gate_vs_source':gate(m,stages[0]['metrics']) if stages else None,'gate_vs_parent':gate(m,next(s['metrics'] for s in stages if s['stage']==parent)) if parent else None};stages.append(row)
  add('source_native',spec['source_frame'],spec['source_proof'],expected=comparison['metrics']['previous_native'])
  for init in ['raw_min','native_retained']:
   warm=E/'wbuart_warm_inputs_v1_2026-10-20'/c['case']/init;warmstates[init]={r['connection_id']:r for r in read(warm/'initial.json')['records']};add(init+'/warm',warm/'initial.json',warm/'verification.json',init,'source_native')
   for policy in ['warm_timing_frozen','warm_timing_round_updated']:
    arm=next(a for a in arms if a['initializer']==init and a['timing_policy']==policy);out=Path(arm['output'])
    for k in [0,1]:
     expected=comparison['metrics']['native_retained_on' if init=='native_retained' else 'raw_min_on'] if policy=='warm_timing_round_updated' and k==1 else None;add(init+'/'+policy+f'/round{k}',out/f'round{k}.json',out/'complete_event_audit.json',init,init+'/warm' if k==0 else init+'/'+policy+'/round0',expected)
  assert len(stages)==11;results.append({'case':c['case'],'stages':stages});print('WBUART_STAGE_DIAGNOSIS',c['case'],len(stages),flush=True)
 assert len(results)==9
 for n,h in bindings.items():assert sha(n)==h
 (D/'verification.json').write_text(json.dumps({'status':'ALL9_99_ORIGINAL_DOMAIN_STAGES_AND_PHYSICAL_OWNER_LEDGERS_RECONSTRUCTED','rows':results,'stages':99,'connections_per_stage':2493,'labels_scores_gates_changed':False,'new_model_or_route_search':False,'scope':'Posthoc diagnosis on exposed development family. Source is past-layout forecast control, not valid current route. No causal or acceptance claim from stage/path-change association.','bindings':bindings},indent=2,default=lambda f:{'numerator':f.numerator,'denominator':f.denominator} if isinstance(f,Fraction) else None)+'\n')
if __name__=='__main__':main()
