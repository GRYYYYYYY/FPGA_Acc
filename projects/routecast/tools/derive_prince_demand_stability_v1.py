"""Every current/previous native demand pair; no final-route labels used."""
import json,struct,math
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
from pre_route_endpoints import sha
from prediction_metrics import spearman
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_demand_stability_v1_2026-10-20'
def rho2(a,b):
 def ranks(v):
  counts=Counter(v);offset=0;lookup={}
  for value,n in sorted(counts.items()):lookup[value]=2*offset+n-1;offset+=n
  return [lookup[x] for x in v]
 x,y=ranks(a),ranks(b);m=len(x)-1;cross=sum((u-m)*(v-m) for u,v in zip(x,y));den=sum((u-m)**2 for u in x)*sum((v-m)**2 for v in y);return cross/math.sqrt(den) if den else None

def main():
 D.mkdir(exist_ok=False);root=E/'prince_resident_phase_trial_v1_2026-10-20';vp=root/'phase_verification_v1.json';v=json.loads(vp.read_text());bindings={str(vp):sha(vp),str(Path(__file__)):sha(__file__)};cases=[];pairs=0
 for row in v['rows']:
  case=row['case'];width=case.split('/')[0];domain=E/'prince_quality_domains_v1_2026-10-20'/width;dp=domain/'verification.json';meta=json.loads(dp.read_text());rp=domain/'resources.jsonl';bp=domain/'spatial_bins.json';resources=list(map(json.loads,rp.open()));bins=json.loads(bp.read_text());assert all(x['capacity']==1 for x in resources);ids=[x['id'] for x in resources];keys=[tuple(x['key']) for x in bins];keyid={key:i for i,key in enumerate(keys)};members=[[keyid[tuple(k)] for k in r['bins']] for r in resources];caps=[x['capacity'] for x in bins];previous=None;previous_tops=None;output=[];source=root/case/'capture/boundary';phase=[list(map(int,line.split())) for line in (source/'phase.tsv').read_text().splitlines()]
  for i,t in enumerate(phase,1):
   path=source/f'iteration_{i}.bin';raw=path.read_bytes();ii,n=struct.unpack_from('<QQ',raw,8);assert ii==i and n==meta['graph_nodes'] and len(raw)==24+24*n;occ=[0]*n
   for index,(nid,kind,count,capacity,word) in enumerate(struct.iter_unpack('<QIiiI',raw[24:])):assert nid==index;occ[nid]=count
   rv=[occ[nid] for nid in ids];counts=[0]*len(keys)
   for demand,span in zip(rv,members):
    if demand:
     for b in span:counts[b]+=demand
   sv=[Q(demand,capacity) for demand,capacity in zip(counts,caps)];current={'resource':rv,'spatial':sv};tops={};metrics={}
   for scope,values,labels,k in [('resource',rv,ids,meta['resource_k']),('spatial',sv,keys,meta['spatial_k'])]:
    order=sorted(range(len(values)),key=lambda j:(-values[j],labels[j]));selected={labels[j] for j in order[:k]};tops[scope]=selected;boundary=values[order[k-1]];record=dict(k=k,boundary_tie_size=sum(x==boundary for x in values),boundary_margin=values[order[k-1]]-values[order[k]])
    if previous is not None:
     rho=spearman(values,previous[scope]);ind=rho2(values,previous[scope]);assert (rho is None)==(ind is None) and (rho is None or abs(rho-ind)<1e-14);record.update(adjacent_spearman=rho,retained_topK=len(selected&previous_tops[scope]),changed_scores=sum(x!=y for x,y in zip(values,previous[scope])),mean_absolute_score_change=sum((abs(x-y) for x,y in zip(values,previous[scope])),Q())/len(values))
    metrics[scope]=record
   output.append(dict(iteration=i,native_overused_nodes=t[2],native_overuse_units=t[3],metrics=metrics));previous=current;previous_tops=tops;pairs+=i>1;bindings[str(path)]=sha(path)
  out=D/case;out.mkdir(parents=True);proof=out/'stability.json';proof.write_text(json.dumps(output,indent=2,default=lambda x:dict(numerator=x.numerator,denominator=x.denominator))+'\n');cases.append(dict(case=case,proof=str(proof),sha256=sha(proof),iterations=len(output)));print('DEMAND_STABILITY',case,len(output),flush=True)
  for path in [dp,rp,bp,source/'phase.tsv']:bindings[str(path)]=sha(path)
 assert pairs==218 and all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=cases,adjacent_pairs=pairs,independent_rank_vectors=2*pairs,bindings=bindings,scope='All9 current/previous demand stability only, full CHANNEL and spatial domains, fixed original TopK ties. No final native target routes or quality labels read; historical development exposure acknowledged. No stability threshold or stopping rule selected.'),indent=2)+'\n')
if __name__=='__main__':main()
