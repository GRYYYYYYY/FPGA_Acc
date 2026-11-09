"""Independent groupby trace parser and propagation count identities."""
import json,sys,itertools
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_iteration_support_observer_v1_2026-10-19';D=E/'prospective_external_family_iteration_support_propagation_v1_2026-10-19';P=E/'prospective_external_family_temporal_prior_errors_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def frames(path):
 with path.open() as f:
  values=(list(map(int,line.split())) for line in f)
  for it,group in itertools.groupby(values,key=lambda r:r[0]):yield it,{r[1]:frozenset(r[3:]) for r in group}

def main():
 s=read(D/'summary.json');assert all(sha(p)==h for p,h in s['bindings'].items());results=[]
 for r in s['rows']:
  case=r['case'];kinds={x['net_id']:bool(x['edit_mask']) for x in read(P/case/'NETs.json')};published=read(D/case/'all_common_iterations.json');previous=set();lasta=lastb=None
  for (it,a),(jt,b),row in zip(frames(I/'source/iteration_support.tsv'),frames(I/case/'iteration_support.tsv'),published):
   assert it==jt==row['iteration'];different={n for n in a if a[n]!=b[n]};clean={n for n in kinds if not kinds[n]};edited=set(kinds)-clean;new=(different-previous)&clean;back=(previous-different)&clean;assert (len(different&clean),len(different&edited),len(new),len(back))==(row['clean_support_different'],row['edited_support_different'],row['new_clean_divergences'],row['reconverged_clean']);assert row['clean_support_different']==len(previous&clean)+len(new)-len(back)
   ua=set().union(*a.values());ub=set().union(*b.values());assert len(ua^ub)==row['global_support_symmetric_difference'];changed=set();exposed=set()
   if lasta is not None:
    ca=Counter(n for ns in lasta.values() for n in ns);cb=Counter(n for ns in lastb.values() for n in ns);oa={n for n,c in ca.items() if c>1};ob={n for n,c in cb.items() if c>1};changed=oa^ob;exposed={n for n in clean if any(x in changed for x in lasta[n]|lastb[n])}
   assert (len(changed),len(exposed),len(new&exposed),len(new-exposed))==(row['prior_different_overuse_nodes'],row['prior_exposed_clean'],row['new_clean_divergences_exposed'],row['new_clean_divergences_unexposed']);previous=different;lasta=a;lastb=b
  assert len(published)==min(r['source_iterations'],r['target_iterations']);assert r['source_unpaired_tail']+len(published)==r['source_iterations'] and r['target_unpaired_tail']+len(published)==r['target_iterations'];results.append(dict(case=case,common_iterations=len(published)))
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL_COMMON_ITERATION_SUPPORT_PROPAGATION_EXPOSURE_AND_TAIL_IDENTITIES_VERIFIED',rows=results,bindings={str(D/'summary.json'):sha(D/'summary.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Independent exact set counts; exposure remains association. No proof of native algorithm causality or model utility.'),f,indent=2)
 print('ALL_PROPAGATION_COUNTS_INDEPENDENTLY_VERIFIED')
if __name__=='__main__':main()
