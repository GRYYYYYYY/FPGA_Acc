"""Descriptive support lower bounds; no predictor fitting or changed quality gates."""
import array,json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];S=10**12

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/mmc_two_bank_invariant_error_v1_2026-10-19';out.mkdir(exist_ok=False)
 cp=R/'experiments/mmc_resource_context_v1_2026-10-19/CHANNEL_ids.u32';ids=array.array('I');ids.frombytes(cp.read_bytes());assert len(ids)==258720 and list(ids)==sorted(ids)
 master=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=read(master);bindings={str(p):sha(p) for p in [cp,master,Path(__file__).resolve()]};rows=[]
 for caseinfo in plan['cases']:
  case=caseinfo['case'];bp=R/f'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/{case}/banks.jsonl';tp=Path(caseinfo['native_label']);assert sha(tp)==plan['bindings'][str(tp)]
  truth={int(n):v for n,v in read(tp)['node_occupancy'].items()};a=Counter();b=Counter();variable=set();nets=set()
  for line in bp.open():
   x=json.loads(line);assert x['net_id'] not in nets;nets.add(x['net_id']);aa=set(x['A']);bb=set(x['B']);a.update(aa);b.update(bb);variable.update(aa^bb)
  assert len(nets)==55300
  groups={'fixed_unowned':[],'fixed_owned':[],'variable':[]}
  for n in ids:groups['variable' if n in variable else 'fixed_owned' if a[n] else 'fixed_unowned'].append(n)
  models={'A':dict(a),'B':dict(b)};paths=[bp,tp]
  for name,rel in [('joint_mean',f'mmc_joint_candidate_ensemble_v1_2026-10-19/{case}/expected_ledger_scaled.json'),('MAP',f'mmc_resource_probability_development_v1_2026-10-19/{case}/history_A_B_prefix_direction_segment/ledger.json'),('target_using_L1_oracle',f'mmc_aggregate_L1_oracle_v1_2026-10-19/{case}/ledger.json')]:
   p=R/'experiments'/rel;paths.append(p);models[name]={int(n):v for n,v in read(p).items()}
  assert all(truth.get(n,0) in (0,1) for n in ids)
  stats={}
  for group,ns in groups.items():
   errors={}
   for name,m in models.items():
    scale=1 if name=='joint_mean' else S
    errors[name]=sum(abs(m.get(n,0)*scale-truth.get(n,0)*S) for n in ns)
   stats[group]=dict(resources=len(ns),native_occupied=sum(truth.get(n,0) for n in ns),L1_scaled=errors)
  fixed=groups['fixed_unowned']+groups['fixed_owned']
  for n in fixed:
   assert a[n]==b[n] and all((m.get(n,0) if name=='joint_mean' else m.get(n,0)*S)==a[n]*S for name,m in models.items())
  bound=sum(abs(a[n]-truth.get(n,0)) for n in fixed)
  assert all(stats['fixed_unowned']['L1_scaled'][name]+stats['fixed_owned']['L1_scaled'][name]==bound*S for name in models)
  total={name:sum(g['L1_scaled'][name] for g in stats.values()) for name in models}
  # Independent error-value histogram reproduces totals without grouped sums.
  for name,m in models.items():
   scale=1 if name=='joint_mean' else S;hist=Counter(abs(m.get(n,0)*scale-truth.get(n,0)*S) for n in ids);assert sum(e*c for e,c in hist.items())==total[name]
  rows.append(dict(case=case,groups=stats,total_L1_scaled=total,scale=S,certified_fixed_support_L1_lower_bound=bound,lower_bound_fraction_of_MAP_error=bound*S/total['MAP'],lower_bound_fraction_of_oracle_error=bound*S/total['target_using_L1_oracle'],scope='Fixed membership is a sufficient invariant subset, not the maximal invariant domain under implication constraints. Lower bound applies to any joint distribution on these original A/B choices, and its mean. Labels are used only for this posthoc diagnostic; no deployable error oracle.'))
  bindings.update({str(p):sha(p) for p in paths});print(case,'fixed_error_bound',bound,'MAP_error',total['MAP']/S,'oracle_error',total['target_using_L1_oracle']/S,'fixed_fraction',bound*S/total['MAP'],flush=True)
 (out/'results.json').write_text(json.dumps(dict(status='ALL3_INVARIANT_MEMBERSHIPS_MODEL_EQUALITIES_AND_ERROR_HISTOGRAMS_VERIFIED',rows=rows,bindings=bindings),indent=2)+'\n')
if __name__=='__main__':main()
