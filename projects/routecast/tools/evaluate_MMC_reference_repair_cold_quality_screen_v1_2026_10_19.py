"""Reference-budget repair occupancy under original cold4metric necessary-control screen; never substitute missing raw_on."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from collections import Counter
from fractions import Fraction
from prediction_metrics import compare
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def serial(x):
 if isinstance(x,Fraction):return str(x)
 if isinstance(x,dict):return {str(k):serial(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [serial(v) for v in x]
 return x
def write(p,j):
 with p.open('x') as f:json.dump(serial(j),f,separators=(',',':'));f.write('\n')
def main():
 M=R/'experiments/mmc_reference_budget_incremental_astar_v2_2026-10-19';ap=M/'independent_verification_v1.json';a=json.loads(ap.read_text());assert a['status']=='ALL3_ACTUAL_LAYOUT_RETAINED_AND_REBUILT_PATHS_REFERENCE_BUDGETS_TRANSACTIONS_AUDITED' and all(c['full_state_complete'] for c in a['cases']);oldframe=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';oldproof=oldframe.parent/'independent_xml_verification_v1.json';sourceproof=json.loads(oldproof.read_text());assert sourceproof['all_native_paths_exact'] and sourceproof['all_uniqueNET_occupancy_matches_full_printed_audit'] and sourceproof['bindings'][str(oldframe)]==sha(oldframe)
 cases=[f'episode_{i:02d}' for i in range(1,4)];I=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19';graph=pathlib.Path(json.loads((I/cases[0]/'demand/endpoints.json').read_text())['inputs']['graph']['path']);assert a['bindings'][str(graph)]==sha(graph);O=R/'experiments/mmc_reference_repair_cold_quality_screen_v1_2026-10-19';O.mkdir();bindings={str(p):sha(p) for p in [ap,oldframe,oldproof,graph,pathlib.Path(__file__).resolve(),R/'tools/prediction_metrics.py']};write(O/'protocol.json',dict(bindings=bindings,cases=cases,domain='All positive CHANX/CHANY plus inclusive-span bins(layer,x,y,type,segment); zeros retained; normalize all scores by resource/bin capacity',metrics='Spearman and deterministic fixed-ID precision: resource top5percent, spatial top20',tie_rule='descending normalized score then ascending numeric RR ID or bin tuple',candidate='reference_budget_repair',necessary_control='previous_native',supplementary_controls=['raw_min_off','native_retained_off'],missing_original_required_control='raw_min_on not generated for these layouts; any previous_native nonregression failure is sufficient to fail original all3case gate, but passing this screen never proves full original gate.',scope='Exposed known MMC development data; original cold-final label semantics distinct from temporal pressure. No replacing original gate with captured future pressure.'))
 channels=[];bins={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:
    nid=int(e.get('id'));loc=e.find('loc');seg=e.find('segment');keys=[]
    for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
     for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):
      key=(int(loc.get('layer','0')),x,y,e.get('type'),int(seg.get('segment_id')) if seg is not None else -1);keys.append(key);bins[key]=bins.get(key,0)+int(e.get('capacity'))
    channels.append((nid,int(e.get('capacity')),keys))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(channels)==258720 and len(bins)==17160;rows=[];source={int(n):v for n,v in json.loads(oldframe.read_text())['ledger'].items()}
 for case in cases:
  cfile=M/case/'model.json';assert a['bindings'][str(cfile)]==sha(cfile);predictions={'reference_budget_repair':{int(n):Fraction(v) for n,v in json.loads(cfile.read_text())['ledger'].items()},'previous_native':source};bindings[str(cfile)]=sha(cfile)
  for label,mode in [('raw_min_off','raw_min'),('native_retained_off','native_retained')]:
   p=R/'experiments/mmc_prospective_swap_initializers_v1_2026-10-19'/case/mode/'initial.json';proof=p.parent.parent/'initial_independent_verification_v1.json';v=json.loads(proof.read_text());assert v['status']=='pass' and v['bindings'][str(p)]==sha(p);predictions[label]={int(n):x for n,x in json.loads(p.read_text())['ledger'].items()};bindings[str(p)]=sha(p);bindings[str(proof)]=sha(proof)
  N=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/case;np=N/'verification.json';nv=json.loads(np.read_text());assert nv['all_native_physical_and_canonical_pass'];lp=N/'cold/physical_audit.json';route=N/'cold/output.route';assert nv['bindings'][str(lp)]==sha(lp) and nv['bindings'][str(route)]==sha(route);truth=json.loads(lp.read_text());assert truth['overflow_units']==0 and truth['all_printed_branch_arc_switch_and_union_checks_pass'] and truth['inputs_sha256']['route']==sha(route) and truth['inputs_sha256']['graph']==sha(graph);actual={int(n):v for n,v in truth['node_occupancy'].items()};bindings.update({str(p):sha(p) for p in [np,lp,route]})
  concrete_truth={n:Fraction(actual.get(n,0),cap) for n,cap,_ in channels};spatial_truth=Counter();spatial_pred={m:Counter() for m in predictions};concrete_pred={m:{} for m in predictions}
  for n,cap,keys in channels:
   assert actual.get(n,0)<=cap
   for model,ledger in predictions.items():concrete_pred[model][n]=Fraction(ledger.get(n,0))/cap
   for key in keys:
    spatial_truth[key]+=actual.get(n,0)
    for model,ledger in predictions.items():spatial_pred[model][key]+=ledger.get(n,0)
  st={key:Fraction(spatial_truth.get(key,0))/cap for key,cap in bins.items()};metrics={}
  for model in predictions:
   sp={key:Fraction(spatial_pred[model].get(key,0))/cap for key,cap in bins.items()};metrics[model]={'concrete':compare(concrete_pred[model],concrete_truth,12936),'spatial':compare(sp,st,20)}
  checks=[]
  for scope in ['concrete','spatial']:
   for metric in ['spearman','precision_at_k']:
    x=metrics['reference_budget_repair'][scope][metric];ref=metrics['previous_native'][scope][metric];eps=1e-12 if metric=='spearman' else 0;checks.append(dict(scope=scope,metric=metric,candidate=x,reference=ref,nonregression=x is not None and ref is not None and x>=ref-eps,strict_improvement=x is not None and ref is not None and x>ref+eps))
  passed=all(x['nonregression'] for x in checks) and any(x['strict_improvement'] for x in checks);rows.append(dict(case=case,metrics=metrics,necessary_control_checks=checks,previous_native_necessary_gate_pass=passed));write(O/(case+'_metrics.json'),rows[-1]);print('COLD NECESSARY CONTROL',case,passed,flush=True)
 status='FAIL_NECESSARY_PREVIOUS_NATIVE_CONTROL' if not all(row['previous_native_necessary_gate_pass'] for row in rows) else 'UNRESOLVED_RAW_MIN_ON_CONTROL_MISSING';write(O/'results.json',dict(status=status,bindings=bindings,cases=rows,resource_domain=258720,spatial_domain=17160,original_full_gate_pass=False,raw_min_on_control_missing=True,independent_verification_pending=True,temporal_pressure_result_unchanged=True,scope='Original4metric necessary-control screen only; failure is sufficient for original all3 gate failure, passing cannot admit full gate. Known exposed data; no family holdout, STA or speed claim.'))
if __name__=='__main__':main()
