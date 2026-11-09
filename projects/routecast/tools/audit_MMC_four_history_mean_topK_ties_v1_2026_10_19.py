"""Prediction-cutoff tie bounds against unchanged fixed-ID truth topK."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_four_archived_layout_mean_prior_v1_2026-10-19';fp=O/'occupancy_sum.json';prior=json.loads(fp.read_text());Q=R/'experiments/mmc_four_history_mean_cold_screen_v1_2026-10-19/results.json';q=json.loads(Q.read_text());graph=next(pathlib.Path(p) for p in q['bindings'] if p.endswith('rr_graph.xml'));assert sha(graph)==prior['graph_sha256'];channels=[];stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:assert int(e.get('capacity'))==1;channels.append(int(e.get('id')))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(channels)==258720;channels.sort();scores={n:int(prior['summed_unique_NET_occupancy'].get(str(n),0)) for n in channels};k=12936;P=sorted(channels,key=lambda n:(-scores[n],n))[:k];cut=scores[P[-1]];above={n for n in channels if scores[n]>cut};tie={n for n in channels if scores[n]==cut};slots=k-len(above);rows=[];bindings={str(p):sha(p) for p in [fp,Q,graph,pathlib.Path(__file__).resolve()]}
 for row in q['cases']:
  case=row['case'];lp=R/'experiments/mmc_prospective_pressure_native_v2_2026-10-19'/case/'cold/physical_audit.json';assert q['bindings'][str(lp)]==sha(lp);truth={int(n):v for n,v in json.loads(lp.read_text())['node_occupancy'].items()};T=set(sorted(channels,key=lambda n:(-truth.get(n,0),n))[:k]);hit=len(tie&T);base=len(above&T);lo=Fraction(base+max(0,slots-(len(tie)-hit)),k);hi=Fraction(base+min(slots,hit),k);observed=Fraction(len(set(P)&T),k);expected=(Fraction(base)+Fraction(slots*hit,len(tie)))/k;reported=row['metrics']['four_history_mean']['concrete']['precision_at_k'];reference=row['metrics']['previous_native']['concrete']['precision_at_k'];assert float(observed)==reported and lo<=observed<=hi
  rows.append(dict(case=case,k=k,prediction_boundary_score=str(Fraction(cut,4)),prediction_boundary_tie_size=len(tie),slots_selected_from_boundary=slots,fixed_truth_topK_boundary_matches=hit,original_fixed_ID_precision=str(observed),prediction_tie_min_precision=str(lo),prediction_tie_max_precision=str(hi),uniform_prediction_tie_expected_precision=str(expected),cannot_repair_previous_native_precision_by_prediction_tie_reordering=float(hi)<reference,original_gate_changed=False));bindings[str(lp)]=sha(lp);print('TOPK_TIE_BOUND',rows[-1],flush=True)
 (O/'topK_prediction_tie_bounds_v1.json').open('x').write(json.dumps(dict(status='ALL3_PREDICTION_TIE_BOUNDS_AGAINST_UNCHANGED_ORIGINAL_TRUTH_TOPK',cases=rows,bindings=bindings,scope='Diagnostic only. Original truth topK remains fixed by numeric RR ID, all original metrics/gates and target labels unchanged. Bounds vary prediction-cutoff ties only, not score weights or truth IDs. Expected tie precision is not a replacement acceptance metric.'),indent=2)+'\n')
if __name__=='__main__':main()
