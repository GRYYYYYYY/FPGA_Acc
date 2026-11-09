"""All node fields and visible NET2 boundary comparison, full original cohort."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from verify_external_full_rr_frontier_v1 import load
from verify_external_initial_response_observer_source_v1 import trees
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_full_rr_frontier_observer_v1_2026-10-19';B=E/'prospective_external_family_early_net_observer_v1_2026-10-19';D=E/'prospective_external_family_full_rr_frontier_comparison_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 audit=read(I/'all_case_frontier_verification_v1.json');assert len(audit['rows'])==4 and all(sha(p)==h for p,h in audit['bindings'].items());D.mkdir(exist_ok=False);oldmeta,old,oldtrees=load(I/'source/rr_frontier.tsv');bindings={str(I/'all_case_frontier_verification_v1.json'):sha(I/'all_case_frontier_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for c in read(I/'target_manifest.json')['cases']:
  case=c['case'];folder=Path(c['output']);meta,new,newtrees=load(folder/'rr_frontier.tsv');assert new.keys()==old.keys();assert trees(folder/'output.route')==trees(B/case/'output.route');counts=Counter();records=[]
  for n in sorted(old):
   a,b=old[n],new[n];assert (a['type'],a['capacity'],a['cost_index'])==(b['type'],b['capacity'],b['cost_index']);fields=[k for k in ['occupancy','history','base','present'] if a[k]!=b[k]]
   for k in fields:counts[a['type'],k]+=1
   records.append(dict(id=n,type=a['type'],on_NET2_prior_support=n in oldtrees[2],changed_fields=fields,old=a,new=b))
  assert oldtrees[2]==newtrees[2];out=D/case;out.mkdir(parents=True);rp=out/'all_RR_comparison.jsonl'
  with rp.open('x') as f:
   for r in records:f.write(json.dumps(r)+'\n')
  row=dict(case=case,nodes=len(records),NET2_full_unique_support_identical=True,final_printed_route_identical=True,boundary_metadata_source=oldmeta,boundary_metadata_target=meta,boundary_metadata_changed=[k for k,a,b in zip(['iteration','order','NET','pres_fac','global_worst_negative_slack','xmin','xmax','ymin','ymax'],oldmeta,meta) if a!=b],counts_by_type_and_field=[dict(type=t,field=k,count=v) for (t,k),v in sorted(counts.items())],nonCHANNEL_occupancy_changed=sum(r['type'] not in ['CHANX','CHANY'] and 'occupancy' in r['changed_fields'] for r in records),NET2_prior_support_occupancy_changed_by_type=dict(Counter(r['type'] for r in records if r['on_NET2_prior_support'] and 'occupancy' in r['changed_fields'])));rows.append(row)
  for p in [rp,folder/'rr_frontier.tsv',folder/'output.route',B/case/'output.route']:bindings[str(p)]=sha(p)
  print(json.dumps(row),flush=True)
 bindings[str(I/'source/rr_frontier.tsv')]=sha(I/'source/rr_frontier.tsv');assert all(sha(p)==h for p,h in bindings.items());(D/'summary.json').write_text(json.dumps(dict(status='ALL3_COMPLETE_RR_FIELD_AND_NET2_VISIBLE_BOUNDARY_COMPARISONS_DONE',rows=rows,bindings=bindings,scope='All129090 nodes per case. Matching printed RR fields/bbox/full unique NET2 support does not imply identical full router state or nonconfigurable-group semantics; native perquery sink-order/budgets/prune flags not captured. Original forecast labels/gates unchanged.'),indent=2)+'\n')
if __name__=='__main__':main()
