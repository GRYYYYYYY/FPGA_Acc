"""Posthoc fixed-domain stage diagnosis; no model search or new scores."""
import sys,json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import defaultdict,Counter
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from external_forecast_metrics_v1 import vectors,metrics,gate
E=R/'experiments';L=E/'prospective_external_family_live_eligibility_trial_v1_2026-10-20';H=E/'prospective_external_family_source_history_trial_v1_2026-10-20';G=E/'prospective_external_family_bound_group_refinement_v1_2026-10-20';D=E/'corrected_epoch_quality_stage_decomposition_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);bindings={str(Path(__file__)):sha(__file__)};admitted={}
 def admit(path):
  path=Path(path).resolve()
  if str(path) in admitted:return admitted[str(path)]
  d=read(path)
  for k,h in d['bindings'].items():
   if k in bindings:assert bindings[k]==h
   else:assert sha(k)==h;bindings[k]=h
  bindings[str(path)]=sha(path);admitted[str(path)]=d;return d
 for folder in [L,H,G]:admit(folder/'research_decision_v1.json')
 cases=read(L/'protocol.json')['cases'];ep=read(cases[0]['endpoint']);graph=Path(ep['inputs']['graph']['path']);dest=array('Q');caps={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if (e.tag,parent)==('node','rr_nodes'):caps[int(e.get('id'))]=int(e.get('capacity'))
  if (e.tag,parent)==('edge','rr_edges'):dest.append(int(e.get('sink_node')))
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 def ledger_from_paths(records):
  owners=defaultdict(set)
  for r in records:owners[r['net_id']].add(r['source']);owners[r['net_id']].update(dest[x] for x in r['answer']['physical_edge_ids'])
  return Counter(n for nodes in owners.values() for n in nodes)
 allrows=[]
 for c in cases:
  case=c['case'];spec=read(L/case/'off/comparison_spec.json');domain=admit(spec['domain_proof']);admit(spec['domain_independent_proof']);label=admit(c['label_proof']);labelpath=Path(c['label_physical_audit']);assert label['bindings'][str(labelpath)]==sha(labelpath);native=read(labelpath);assert native['overflow_units']==0;folder=Path(spec['domain_proof']).parent;resources=[json.loads(x) for x in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');truth=vectors(resources,bins,{int(n):v for n,v in native['node_occupancy'].items()},len(caps),truth=True);expected=read(L/case/'off/comparison.json')['metrics'];stages=[]
  def add(name,path,proof,init=None,parent=None,expected_metrics=None):
   path=Path(path).resolve();p=admit(proof);assert p['bindings'][str(path)]==sha(path);f=read(path);records=f['records'];assert len(records)==15616 and len({r['connection_id'] for r in records})==15616;ledger=ledger_from_paths(records);assert ledger==Counter({int(n):v for n,v in f['ledger'].items()});m=metrics(vectors(resources,bins,dict(ledger),len(caps)),truth,domain['resource_k'],domain['spatial_k']);small={s:{k:v for k,v in data.items() if k in ['spearman','top_k_hits','k','universe_size','precision_at_k','recall_at_k','mae']} for s,data in m.items()}
   if expected_metrics is not None:
    for s in ['resource','spatial']:assert abs(m[s]['spearman']-expected_metrics[s]['spearman'])<1e-12 and m[s]['top_k_hits']==expected_metrics[s]['top_k_hits']
   changed_NETs=changed_CIDs=None
   if init is not None:
    warm=read(Path(c['warm'])/init/'initial.json');old={r['connection_id']:(r['source'],tuple(r['answer']['physical_edge_ids'])) for r in warm['records']};changed=[r for r in records if old[r['connection_id']]!=(r['source'],tuple(r['answer']['physical_edge_ids']))];changed_CIDs=len(changed);changed_NETs=len({r['net_id'] for r in changed})
   row=dict(stage=name,frame=str(path),proof=str(Path(proof).resolve()),initializer=init,parent_stage=parent,metrics=small,changed_CIDs_from_warm=changed_CIDs,changed_NETs_from_warm=changed_NETs,overflow=sum(max(0,v-caps[n]) for n,v in ledger.items()),gate_vs_source=None,gate_vs_parent=None)
   if stages:row['gate_vs_source']=gate(m,stages[0]['metrics'])
   if parent is not None:row['gate_vs_parent']=gate(m,next(r['metrics'] for r in stages if r['stage']==parent))
   stages.append(row)
  add('source_native',c['source_frame'],c['source_proof'],expected_metrics=expected['previous_native'])
  for init in ['raw_min','native_retained']:
   warm=Path(c['warm'])/init;add(init+'/warm',warm/'initial.json',warm/'verification.json',init,'source_native')
   for policy,base,arm in [('all_NET',L,'off'),('source_history',H,'on'),('live_eligibility',L,'on')]:
    out=base/case/init/arm
    for round in [0,1]:
     final_expected=expected['native_retained_on' if init=='native_retained' else 'raw_min_on'] if policy=='all_NET' and round==1 else None
     add(init+'/'+policy+f'/round{round}',out/f'round{round}.json',out/'complete_event_audit.json',init,init+'/warm' if round==0 else init+'/'+policy+'/round0',final_expected)
  for arm,policy in [('off','group_zero_bound'),('on','group_compact_bound')]:
   out=G/case/arm;add('native_retained/'+policy,out/'final_round.json',out/'complete_event_audit.json','native_retained','native_retained/all_NET/round1')
  allrows.append(dict(case=case,stages=stages));print('STAGES_COMPLETE',case,len(stages),flush=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_ORIGINAL_LABEL_DOMAIN_STAGE_QUALITY_AND_PATH_LEDGER_DECOMPOSITION_COMPLETE',rows=allrows,bindings=bindings,scope='Posthoc diagnosis only on all3 exposed cases. Same native cold labels, full resources/bins/K, exact capacity normalization and registered four-metric gate. Original source frame is a past-placement control. No new predictor, score transform, case selection, native utility or quality promotion.'),indent=2,default=lambda x:dict(numerator=x.numerator,denominator=x.denominator) if isinstance(x,Fraction) else None)+'\n')
if __name__=='__main__':main()
