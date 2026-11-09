"""Retrospective fixed-group mass and binary-truth topK decomposition.

Original deterministic metric and failed gates are retained. Positive-label rate
is auxiliary, not a corrected/replacement primary metric or calibrated risk.
"""
import hashlib,json
from array import array
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(info):
 assert sha(info['path'])==info['sha256'];a=array('d');a.frombytes(Path(info['path']).read_bytes());assert len(a)==info['values'];return a

def main():
 out=Path('experiments/mmc_anchored_group_mass_diagnosis_v2_2026-10-18');out.mkdir(exist_ok=False)
 prior=Path('experiments/mmc_pressure_risk_matrix_v1_2026-10-18');manifest=json.loads((prior/'vector_manifest.json').read_text());domains=json.loads((prior/'domains.json').read_text());nodes=domains['ids']['channels'];K=len(nodes)//20
 gp=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18/groups.json');g=json.loads(gp.read_text());groups={i:row for i,row in enumerate(g['groups']) if row['kind']=='geometry_channel'};nodegroup={n:i for i,row in groups.items() for n in row['members']};assert set(nodes)==set(nodegroup)
 source=Path('experiments/mmc_anchored_NET_forecasts_v1_2026-10-18');plan=json.loads((source/'protocol.json').read_text());newmanifest=json.loads((source/'vector_manifest.json').read_text());index={n:i for i,n in enumerate(g['positive_RR_ids'])}
 sourceproofpath=Path('experiments/mmc_anchored_NET_forecasts_verification_v1_2026-10-18/verification.json');sp=json.loads(sourceproofpath.read_text());assert sp['status']=='pass';metricproof=Path('experiments/mmc_anchored_outcomes_verification_v1_2026-10-18/verification.json');mp=json.loads(metricproof.read_text());assert mp['status']=='pass'
 bindings={str(p.resolve()):sha(p) for p in [gp,prior/'domains.json',prior/'vector_manifest.json',source/'protocol.json',source/'vector_manifest.json',sourceproofpath,metricproof,Path(__file__)]}
 # Source vector bindings are admitted by the independent pressure proof.
 oldproofpath=Path('experiments/mmc_typed_risk_matrix_verification_v1_2026-10-18/verification.json');oldproof=json.loads(oldproofpath.read_text());assert oldproof['status']=='pass';bindings[str(oldproofpath.resolve())]=sha(oldproofpath)
 for case in plan['cases']:
  base=Path('experiments/mmc_multiplacement_quality_v1_2026-10-18')/case;proof=json.loads((base/'verification.json').read_text());assert proof['status']=='pass'
  for p in [base/'vectors.json',base/'comparison.json']:assert sha(p)==proof['bindings'][str(p.resolve())];bindings[str(p.resolve())]=sha(p)
  bindings[str((base/'verification.json').resolve())]=sha(base/'verification.json')
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,cases=plan['cases'],sources=plan['sources'],primary_source='native_retained_on',K=K,group_definition='Unchanged original geometry/direction/segment/RC groups.',diagnostics=['Exact source/cold group masses, L1 sum of group residuals as a universal fixed-mass prediction lower bound.','Source point, uniform group mean and fixed half anchored mean node L1.','Deterministic predicted topK overlap with deterministic binary-truth topK versus selected positive-label count, full truth-boundary tie interval.','TopK selection/mass by graph-only group cardinality.'],bound='For each group, sum_n|p_n-y_n|>=|sum_np_n-sum_ny_n|. Summing groups gives a floor for any nonnegative predictor preserving group masses. Sharp in an unconstrained nonnegative vector class, not a physically legal path class.',scope='Retrospective exposed development diagnosis only. Auxiliary binary-positive hit rate does not replace original primary topK overlap or change failed gates. No mixture fitting, target selection or causality/native utility claim.'),f,indent=2)
 rows=[]
 for case in plan['cases']:
  original=json.loads(Path('experiments/mmc_multiplacement_quality_v1_2026-10-18',case,'vectors.json').read_text());assert [r['node'] for r in original['channels']]==nodes
  truth={r['node']:r['labels']['cold'] for r in original['channels']};assert all(r['capacity']==1 and r['labels']['cold'] in [0,1] for r in original['channels']);positive=sum(truth.values());truth_top=set(n for n in nodes if truth[n]);truth_top=set(sorted(truth_top)[:K]);assert len(truth_top)==K
  targetmass={gid:sum(truth[n] for n in row['members']) for gid,row in groups.items()}
  for method in plan['sources']:
   info=manifest[case+'__'+method+'__channels'];assert info['sha256']==oldproof['bindings'][info['path']];raw=read(info);assert all(x.is_integer() for x in raw);point=dict(zip(nodes,map(int,raw)));bindings[info['path']]=info['sha256']
   jpath=source/(case+'__'+method+'.json');assert sha(jpath)==sp['bindings'][str(jpath.resolve())];journal=json.loads(jpath.read_text())['group_totals'];bindings[str(jpath.resolve())]=sha(jpath)
   ainfo=newmanifest[case+'__'+method+'__anchored_group_mean'];assert ainfo['sha256']==sp['bindings'][ainfo['path']];full=read(ainfo);bindings[ainfo['path']]=ainfo['sha256']
   source_mass={gid:sum(point[n] for n in row['members']) for gid,row in groups.items()};lower=sum(abs(source_mass[gid]-targetmass[gid]) for gid in groups);increase=sum(max(0,targetmass[gid]-source_mass[gid]) for gid in groups);decrease=sum(max(0,source_mass[gid]-targetmass[gid]) for gid in groups)
   assert increase+decrease==lower and increase-decrease==sum(targetmass.values())-sum(source_mass.values())
   exact={};uniform={}
   for gid,row in groups.items():
    ns=row['members'];m=len(ns);S=source_mass[gid];assert Fraction(journal.get(str(gid),{}).get('expected_occupancy_total','0'))==S
    for n in ns:
     uniform[n]=Fraction(S,m);exact[n]=Fraction(point[n],2)+Fraction(S,2*m);assert float(exact[n])==full[index[n]]
    assert sum(exact[n] for n in ns)==S
   model_summaries={}
   for label,values in [('source_point',point),('uniform_group_mean',uniform),('half_anchored_mean',exact)]:
    l1=sum((abs(values[n]-truth[n]) for n in nodes),Fraction(0));assert l1>=lower
    # Sort persisted float values to retain original vector metric semantics.
    selected=sorted(nodes,key=lambda n:(-float(values[n]),n))[:K];positive_hits=sum(truth[n] for n in selected);hits=len(set(selected)&truth_top);cut=float(values[selected[-1]]);above=sum(float(v)>cut for v in values.values());equal=sum(float(v)==cut for v in values.values());assert above<K<=above+equal
    lowerhits=max(0,K-(positive-positive_hits));upperhits=min(K,positive_hits)
    assert lowerhits<=hits<=upperhits and hits<=positive_hits
    bysize=defaultdict(lambda:Counter(selected=0,positive_hits=0,deterministic_hits=0,source_group_mass=0,cold_group_mass=0));selected_groups=Counter(nodegroup[n] for n in selected)
    for n in selected:
     gid=nodegroup[n];m=len(groups[gid]['members']);bysize[m]['selected']+=1;bysize[m]['positive_hits']+=truth[n];bysize[m]['deterministic_hits']+=n in truth_top
    for gid in selected_groups:
     m=len(groups[gid]['members']);bysize[m]['source_group_mass']+=source_mass[gid];bysize[m]['cold_group_mass']+=targetmass[gid]
    model_summaries[label]=dict(L1=str(l1),MAE=float(l1/len(nodes)),fixed_group_mass_lower_bound=str(lower),excess_L1_above_group_bound=str(l1-lower),predicted_topK=dict(k=K,deterministic_hits=hits,deterministic_precision=hits/K,binary_positive_hits=positive_hits,auxiliary_binary_positive_rate=positive_hits/K,positive_hits_outside_deterministic_truth_topK=positive_hits-hits,fixed_prediction_truth_tie_hit_interval=[lowerhits,upperhits],truth_equal_boundary=positive,prediction_boundary=cut,prediction_strictly_above=above,prediction_equal_boundary=equal),by_group_size=dict(bysize))
   rows.append(dict(case=case,source=method,channels=len(nodes),groups=len(groups),source_channel_mass=sum(source_mass.values()),cold_channel_mass=sum(targetmass.values()),changed_mass_groups=sum(source_mass[gid]!=targetmass[gid] for gid in groups),overfull_source_groups=sum(source_mass[gid]>len(row['members']) for gid,row in groups.items()),mass_increase_needed=increase,mass_decrease_needed=decrease,group_mass_L1=lower,group_mass_MAE_lower_bound=lower/len(nodes),models=model_summaries));print('GROUP MASS DIAGNOSIS DONE',case,method,flush=True)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'diagnosis.json').open('x') as f:json.dump(dict(status='all18_group_mass_and_topK_decompositions_computed_independent_audit_pending',bindings=bindings,rows=rows,scope='Auxiliary exposed-mechanism diagnosis only; original failed gates unchanged.'),f,indent=2)
if __name__=='__main__':main()
