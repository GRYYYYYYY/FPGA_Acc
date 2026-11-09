"""Streaming exact common-horizon propagation; unequal tails remain explicitly counted."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_iteration_support_observer_v1_2026-10-19';P=E/'prospective_external_family_temporal_prior_errors_v1_2026-10-19';D=E/'prospective_external_family_iteration_support_propagation_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def snapshots(path):
 group={};last=1
 with path.open() as stream:
  for line in stream:
   x=list(map(int,line.split()));it,net,count=x[:3];assert count==len(x)-3
   if it!=last:yield last,group;group={};last=it
   assert net not in group;group[net]=set(x[3:])
 if group:yield last,group

def main():
 receipt=read(I/'all_case_trace_verification_v1.json');assert len(receipt['rows'])==4 and all(sha(p)==h for p,h in receipt['bindings'].items());equiv=read(I/'all_case_verification_v1.json');assert all(r['final_route_identical'] for r in equiv['rows']);D.mkdir(exist_ok=False);bindings={str(I/'all_case_trace_verification_v1.json'):sha(I/'all_case_trace_verification_v1.json'),str(I/'all_case_verification_v1.json'):sha(I/'all_case_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)};summaries=[]
 for c in read(I/'target_manifest.json')['cases']:
  case=c['case'];source=I/'source/iteration_support.tsv';target=Path(c['output'])/'iteration_support.tsv';classes={r['net_id']:bool(r['edit_mask']) for r in read(P/case/'NETs.json')};clean={n for n,k in classes.items() if not k};edited=set(classes)-clean;prev_diff=set();prev_a=prev_b=None;output=[]
  for (it,a),(jt,b) in zip(snapshots(source),snapshots(target)):
   assert it==jt and a.keys()==b.keys()==classes.keys();diff={n for n in a if a[n]!=b[n]};new_clean=(diff-prev_diff)&clean;exposed=set();changed_overuse=set()
   if prev_a is not None:
    oa=Counter(x for ns in prev_a.values() for x in ns);ob=Counter(x for ns in prev_b.values() for x in ns);changed_overuse={x for x in oa.keys()|ob.keys() if (oa[x]>1)!=(ob[x]>1)}
    exposed={n for n in clean if (prev_a[n]|prev_b[n])&changed_overuse}
   ca=Counter(x for ns in a.values() for x in ns);cb=Counter(x for ns in b.values() for x in ns);support_changed=sum((ca[x]>0)!=(cb[x]>0) for x in ca.keys()|cb.keys());output.append(dict(iteration=it,clean_support_different=len(diff&clean),edited_support_different=len(diff&edited),new_clean_divergences=len(new_clean),reconverged_clean=len((prev_diff-diff)&clean),global_support_symmetric_difference=support_changed,prior_different_overuse_nodes=len(changed_overuse),prior_exposed_clean=len(exposed),new_clean_divergences_exposed=len(new_clean&exposed),new_clean_divergences_unexposed=len(new_clean-exposed)));prev_diff=diff;prev_a=a;prev_b=b
  source_n=read(I/'source/verification.json')['iterations'];target_n=read(Path(c['output'])/'verification.json')['iterations'];assert len(output)==min(source_n,target_n);out=D/case;out.mkdir(parents=True);path=out/'all_common_iterations.json';path.write_text(json.dumps(output,indent=2)+'\n');milestones={}
  for numerator in [1,10,50,90]:
   found=next((r['iteration'] for r in output if 100*r['clean_support_different']>=numerator*len(clean)),None);milestones[str(numerator)+'_percent_clean_NETs']=found
  row=dict(case=case,source_iterations=source_n,target_iterations=target_n,common_iterations=len(output),source_unpaired_tail=max(0,source_n-target_n),target_unpaired_tail=max(0,target_n-source_n),clean_NETs=len(clean),milestones=milestones,first=output[0],last_common=output[-1],scope='Overuse exposure uses previous-iteration symmetric difference of overcapacity CHANNEL identities and previous source/target cleanNET supports. Exposure association is not causality; unexposed does not rule out indirect/timing propagation.');summaries.append(row)
  for p in [path,source,target,P/case/'NETs.json']:bindings[str(p)]=sha(p)
  print(json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'summary.json').write_text(json.dumps(dict(status='ALL3_EXACT_COMMON_HORIZON_PROPAGATION_MEASURED_UNEQUAL_TAILS_RETAINED',rows=summaries,bindings=bindings),indent=2)+'\n')
if __name__=='__main__':main()
