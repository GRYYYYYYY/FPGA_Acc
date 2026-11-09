"""Post-evaluation diagnosis only; no fitted model, gate, or prediction changes."""
import json,array,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/mmc_joint_ensemble_topK_diagnosis_v1_2026-10-19';out.mkdir(exist_ok=False)
 cp=R/'experiments/mmc_resource_context_v1_2026-10-19/CHANNEL_ids.u32';ids=array.array('I');ids.frombytes(cp.read_bytes());assert len(ids)==258720
 qp=R/'experiments/mmc_joint_candidate_ensemble_quality_v1_2026-10-19/results.json';q=read(qp)
 master=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=read(master);bindings={str(p):sha(p) for p in [cp,qp,master,Path(__file__).resolve()]};rows=[];scale=10**12;k=12936
 for item in plan['cases']:
  case=item['case'];bank=R/f'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/{case}/banks.jsonl';jp=R/f'experiments/mmc_joint_candidate_ensemble_v1_2026-10-19/{case}/expected_ledger_scaled.json';mp=R/f'experiments/mmc_resource_probability_development_v1_2026-10-19/{case}/history_A_B_prefix_direction_segment/ledger.json';tp=Path(item['native_label'])
  assert plan['bindings'][str(tp)]==sha(tp)
  joint={int(n):v for n,v in read(jp).items()};point={int(n):v for n,v in read(mp).items()};truth={int(n):v for n,v in read(tp)['node_occupancy'].items()};assert all(truth.get(n,0) in (0,1) for n in ids)
  variable=set();a=Counter();b=Counter()
  for line in bank.open():
   z=json.loads(line);aa=set(z['A']);bb=set(z['B']);a.update(aa);b.update(bb);variable.update(aa^bb)
  # No covariance/independence assumptions needed for these fixed memberships.
  assert all(joint.get(n,0)==a[n]*scale and a[n]==b[n] for n in ids if n not in variable)
  ttop=set(sorted(ids,key=lambda n:(-truth.get(n,0),n))[:k]);jt=set(sorted(ids,key=lambda n:(-joint.get(n,0),n))[:k]);mt=set(sorted(ids,key=lambda n:(-point.get(n,0),n))[:k]);jhit=len(jt&ttop);mhit=len(mt&ttop)
  prior=next(r for r in q['rows'] if r['case']==case)['precision_results']['float_primary'];assert abs(jhit/k-prior['metrics']['concrete']['precision_at_k'])<1e-15
  checks=prior['comparisons']['paired_MAP']['checks'];ref=next(c['reference'] for c in checks if (c['scope'],c['metric'])==('concrete','precision_at_k'));assert abs(mhit/k-ref)<1e-15
  groups={}
  for name,s in [('joint_only',jt-mt),('MAP_only',mt-jt),('shared',jt&mt)]:
   counts=Counter(('variable' if n in variable else 'fixed', 'truth_topK' if n in ttop else 'truth_occupied_outside_topK' if truth.get(n,0) else 'truth_empty') for n in s)
   groups[name]={'size':len(s),'counts':{'/'.join(key):v for key,v in sorted(counts.items())}}
  # Set-difference identity independently accounts every lost/gained topK hit.
  lost=len((mt-jt)&ttop);gained=len((jt-mt)&ttop);assert jhit-mhit==gained-lost
  row=dict(case=case,joint_hits=jhit,MAP_hits=mhit,net_hit_delta=jhit-mhit,lost_hits=lost,gained_hits=gained,groups=groups,variable_CHANNELs=sum(n in variable for n in ids),fixed_CHANNELs=sum(n not in variable for n in ids),joint_predicted_boundary=sorted((joint.get(n,0),-n) for n in jt)[0][0],scope='Posthoc set accounting only; fixed means no NET A/B membership change, not a prediction correctness claim. No parameter tuning or causal attribution.')
  rows.append(row);bindings.update({str(p):sha(p) for p in [bank,jp,mp,tp]});print(case,jhit,mhit,'delta',jhit-mhit,flush=True)
 (out/'results.json').write_text(json.dumps(dict(status='ALL3_TOPK_SET_DIFFERENCES_AND_FIXED_BANK_MEMBERSHIPS_ACCOUNTED',rows=rows,bindings=bindings),indent=2)+'\n')
if __name__=='__main__':main()
