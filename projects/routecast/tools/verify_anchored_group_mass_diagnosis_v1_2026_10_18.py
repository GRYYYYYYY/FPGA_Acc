"""Independent contingency-table L1 and heap topK replay, with bound fixtures."""
import hashlib,heapq,itertools,json
from array import array
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(info):
 assert sha(info['path'])==info['sha256'];a=array('d');a.frombytes(Path(info['path']).read_bytes());assert len(a)==info['values'];return a

def main():
 root=Path('experiments/mmc_anchored_group_mass_diagnosis_v2_2026-10-18');dp=root/'diagnosis.json';d=json.loads(dp.read_text());assert d['status']=='all18_group_mass_and_topK_decompositions_computed_independent_audit_pending'
 out=Path('experiments/mmc_anchored_group_mass_verification_v1_2026-10-18');out.mkdir(exist_ok=False)
 bindings={**d['bindings'],str(dp.resolve()):sha(dp),str((root/'protocol.json').resolve()):sha(root/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)}
 for p,h in bindings.items():assert sha(p)==h
 # Exhaustive fractional-grid triangle bounds and explicit sharpness construction.
 bound_cases=0;sharp_cases=0
 for size in range(1,5):
  for truth in itertools.product([0,1],repeat=size):
   target=sum(truth)
   for pred in itertools.product([Fraction(0),Fraction(1,2),Fraction(1),Fraction(3,2)],repeat=size):
    assert sum(abs(a-b) for a,b in zip(pred,truth))>=abs(sum(pred)-target);bound_cases+=1
   for twice_mass in range(2*size+3):
    mass=Fraction(twice_mass,2);pred=[Fraction(0)]*size;remaining=mass
    for i,y in enumerate(truth):
     if y:pred[i]=min(Fraction(1),remaining);remaining-=pred[i]
    if remaining:pred[0]+=remaining
    assert sum(pred)==mass and sum(abs(a-b) for a,b in zip(pred,truth))==abs(mass-target);sharp_cases+=1
 gp=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/groups.json');g=json.loads(gp.read_text());groups={i:r['members'] for i,r in enumerate(g['groups']) if r['kind']=='geometry_channel'};nodes=sorted(n for ns in groups.values() for n in ns);idx={n:i for i,n in enumerate(nodes)};group_indices={gid:[idx[n] for n in ns] for gid,ns in groups.items()};nodegroup={idx[n]:gid for gid,ns in groups.items() for n in ns};fullindex={n:i for i,n in enumerate(g['positive_RR_ids'])};K=len(nodes)//20
 prior=Path('experiments/mmc_pressure_risk_matrix_v1_2026-10-18');manifest=json.loads((prior/'vector_manifest.json').read_text());source=Path('experiments/mmc_anchored_NET_forecasts_v1_2026-10-18');sm=json.loads((source/'vector_manifest.json').read_text());plan=json.loads((source/'protocol.json').read_text())
 assert {(r['case'],r['source']) for r in d['rows']}==set(itertools.product(plan['cases'],plan['sources'])) and len(d['rows'])==18
 newcoldpath=Path('experiments/mmc_anchored_cold_quality_v1_2026-10-18/results.json');newcold=json.loads(newcoldpath.read_text());metricproof=json.loads(Path('experiments/mmc_anchored_outcomes_verification_v1_2026-10-18/verification.json').read_text());assert sha(newcoldpath)==metricproof['bindings'][str(newcoldpath.resolve())];bindings[str(newcoldpath.resolve())]=sha(newcoldpath)
 for case in plan['cases']:
  original=json.loads(Path('experiments/mmc_multiplacement_quality_v1_2026-10-18',case,'vectors.json').read_text());assert [x['node'] for x in original['channels']]==nodes;truth=[x['labels']['cold'] for x in original['channels']];assert set(truth)<={0,1};positive=sum(truth);truth_selected=set(heapq.nsmallest(K,(i for i,v in enumerate(truth) if v)))
  for method in plan['sources']:
   row=next(r for r in d['rows'] if r['case']==case and r['source']==method);raw=read(manifest[case+'__'+method+'__channels']);point=[int(x) for x in raw];assert raw==array('d',point);uniform=read(manifest[case+'__pooled_'+method+'__channels']);full=read(sm[case+'__'+method+'__anchored_group_mean']);anchored=array('d',(full[fullindex[n]] for n in nodes))
   mass={gid:sum(point[i] for i in ii) for gid,ii in group_indices.items()};target={gid:sum(truth[i] for i in ii) for gid,ii in group_indices.items()};bound=sum(abs(mass[gid]-target[gid]) for gid in groups);errors={name:Fraction(0) for name in ['source_point','uniform_group_mean','half_anchored_mean']}
   for gid,ii in group_indices.items():
    size=len(ii);S=mass[gid];table=Counter((point[i],truth[i]) for i in ii)
    errors['source_point']+=sum(count*abs(p-y) for (p,y),count in table.items());errors['uniform_group_mean']+=Fraction(sum(count*abs(S-size*y) for (p,y),count in table.items()),size);errors['half_anchored_mean']+=Fraction(sum(count*abs(p*size+S-2*size*y) for (p,y),count in table.items()),2*size)
    assert all(uniform[i]==float(Fraction(S,size)) and anchored[i]==float(Fraction(point[i]*size+S,2*size)) for i in ii)
   expected=dict(channels=len(nodes),groups=len(groups),source_channel_mass=sum(point),cold_channel_mass=positive,changed_mass_groups=sum(mass[gid]!=target[gid] for gid in groups),overfull_source_groups=sum(mass[gid]>len(groups[gid]) for gid in groups),mass_increase_needed=sum(max(0,target[gid]-mass[gid]) for gid in groups),mass_decrease_needed=sum(max(0,mass[gid]-target[gid]) for gid in groups),group_mass_L1=bound,group_mass_MAE_lower_bound=bound/len(nodes))
   for k,value in expected.items():assert row[k]==value,(case,method,k)
   for label,values in [('source_point',raw),('uniform_group_mean',uniform),('half_anchored_mean',anchored)]:
    r=row['models'][label];err=errors[label];assert Fraction(r['L1'])==err and r['MAE']==float(err/len(nodes)) and Fraction(r['excess_L1_above_group_bound'])==err-bound and Fraction(r['fixed_group_mass_lower_bound'])==bound
    chosen=heapq.nsmallest(K,range(len(nodes)),key=lambda i:(-values[i],i));hits=len(set(chosen)&truth_selected);used=sum(truth[i] for i in chosen);cut=min(values[i] for i in chosen);top=r['predicted_topK'];e=dict(k=K,deterministic_hits=hits,deterministic_precision=hits/K,binary_positive_hits=used,auxiliary_binary_positive_rate=used/K,positive_hits_outside_deterministic_truth_topK=used-hits,fixed_prediction_truth_tie_hit_interval=[max(0,K-positive+used),min(K,used)],truth_equal_boundary=positive,prediction_boundary=cut,prediction_strictly_above=sum(x>cut for x in values),prediction_equal_boundary=sum(x==cut for x in values));assert top==e
    sizes=defaultdict(lambda:Counter(selected=0,positive_hits=0,deterministic_hits=0,source_group_mass=0,cold_group_mass=0));selected_groups=set()
    for i in chosen:
     gid=nodegroup[i];selected_groups.add(gid);size=len(groups[gid]);sizes[size].update(dict(selected=1,positive_hits=truth[i],deterministic_hits=int(i in truth_selected)))
    for gid in selected_groups:sizes[len(groups[gid])].update(dict(source_group_mass=mass[gid],cold_group_mass=target[gid]))
    assert r['by_group_size']=={str(k):dict(v) for k,v in sizes.items()}
   c=next(x['metrics'] for x in newcold['rows'] if x['case']==case and x['source']==method and x['domain']=='concrete');r=row['models']['half_anchored_mean'];assert c['precision_at_k']==r['predicted_topK']['deterministic_precision'] and abs(c['mae']-r['MAE'])<1e-12
   print('INDEPENDENT MASS/TIE REPLAY PASS',case,method,flush=True)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows_verified=18,model_decompositions_verified=54,bound_grid_cases=bound_cases,sharp_unconstrained_bound_cases=sharp_cases,scope='Independent contingency-table exact L1, heap-based topK, complete group-size decompositions and archived metric identity. Lower bound applies to fixed group masses, sharp only for unconstrained nonnegative vectors. Auxiliary positive-label rate does not replace the original metric or gates.'),f,indent=2)
 print('ALL18 MASS AND TIE DIAGNOSES VERIFIED',flush=True)
if __name__=='__main__':main()
