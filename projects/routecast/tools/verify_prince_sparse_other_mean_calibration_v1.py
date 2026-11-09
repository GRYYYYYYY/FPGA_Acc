"""Independent physical-route targets, fold exclusion and pointwise exact Brier audit."""
import json,struct
from pathlib import Path
from collections import Counter
from fractions import Fraction
from pre_route_endpoints import sha
from evaluate_prince_ready_owner_forecast_v1 import final_owners
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_sparse_other_arrival_v1_2026-10-20';D=E/'prince_sparse_other_mean_calibration_v1_2026-10-20'
def bits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def number(word):return Fraction(struct.unpack('<f',struct.pack('<I',word))[0])
def main():
 vp=D/'verification.json';mp=D/'models.json';source=S/'verification.json';v=json.loads(vp.read_text());models=json.loads(mp.read_text());assert sha(mp)==v['models_sha256'];bindings={str(p):sha(p) for p in [vp,mp,source,Path(__file__)]};data={}
 for row in json.loads(source.read_text())['rows']:
  if not row['available']:continue
  case=row['case'];route=E/'prince_native_cohort_v1_2026-10-20'/case/'output.route';owners=final_owners(route);inverse={node:net for net,nodes in owners.items() for node in nodes};records={};inp=Path(row['input_path']);assert sha(inp)==row['input_sha256']
  for net,node,connection,own,ready,n in map(json.loads,inp.open()):
   key=(own,net,node);y=int(node in inverse and inverse[node]!=net)
   if key in records:assert records[key][0:2]==(ready,y);records[key]=(ready,y,records[key][2]+n)
   else:records[key]=(ready,y,n)
  data[case]=records;bindings[str(route)]=sha(route);bindings[str(inp)]=sha(inp)
 rows=[]
 for model in models['folds']:
  held=model['heldout_episode'];train=set(model['train_cases']);test=set(model['test_cases']);assert train=={case for case in data if case.split('/')[1]!=held};assert test==set(data)-train and len(train)==4 and len(test)==2;bin_n=Counter();bin_p=Counter();base_n=Counter();base_p=Counter()
  for case in train:
   for (own,net,node),(ready,y,n) in data[case].items():bin_n[own,ready]+=1;bin_p[own,ready]+=y;base_n[own]+=1;base_p[own]+=y
  for own in [0,1]:
   n=base_n[own];p=base_p[own];assert n>0;expected=bits((p+1)/(n+2));assert model['I_only_words'][str(own)]==expected
   for ready in [0,1]:
    n=bin_n[own,ready];p=bin_p[own,ready];key=f'{own},{ready}';assert model['cell_counts'][key]['states']==n and model['cell_counts'][key]['positive_states']==p;expected=bits((p+1)/(n+2)) if n else model['I_only_words'][str(own)];assert expected==model['I_ready_words'][key]
  for case in sorted(test):
   expected=next(x for x in v['rows'] if x['case']==case);sums={weight:{name:Fraction(0) for name in ['zero','hard_ready','I_only','I_ready']} for weight in ['calls','states']};nstate=ncall=0;cache={}
   for (own,net,node),(ready,y,n) in data[case].items():
    words={'zero':0,'hard_ready':bits(float(ready)),'I_only':model['I_only_words'][str(own)],'I_ready':model['I_ready_words'][f'{own},{ready}']}
    for name,w in words.items():
     key=(w,y)
     if key not in cache:cache[key]=(number(w)-y)**2
     sums['states'][name]+=cache[key];sums['calls'][name]+=n*cache[key]
    nstate+=1;ncall+=n
   for weight,n in [('states',nstate),('calls',ncall)]:
    assert expected[weight]['observations']==n
    for name,value in sums[weight].items():assert Fraction(*expected[weight]['exact_error_sums'][name])==value and expected[weight]['Brier'][name]==float(value/n)
   rows.append(dict(case=case,heldout_episode=held,training_cases=sorted(train),no_same_episode_training_case=True,states=nstate,calls=ncall,pointwise_exact_scores_reconciled=True))
 assert len(rows)==6 and all(sha(p)==h for p,h in bindings.items());out=D/'independent_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL6_GROUP_EXCLUSION_TABLE_WORDS_AND_BRIER_SCORES_RECONCILED',rows=rows,bindings=bindings,method='Original printed legal physical routes instead of terminal binary labels; independently rebuilt state deduplication, fold cell counts/binary32 words; pointwise rational squared errors instead of aggregate polynomial scoring.'),indent=2)+'\n');print('EXPECTED_MEAN_INDEPENDENT_PASS',len(rows))
if __name__=='__main__':main()
