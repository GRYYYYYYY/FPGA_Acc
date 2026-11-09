"""Fixed four-cell expected-demand calibration; whole-episode grouped development holdout."""
import json,struct
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from verify_prince_ready_owner_forecast_v1 import final_inverse,L
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_sparse_other_arrival_v1_2026-10-20';D=E/'prince_sparse_other_mean_calibration_v1_2026-10-20'
def word(q):return struct.unpack('<I',struct.pack('<f',float(q)))[0]
def ratio(bits):return Fraction(struct.unpack('<f',struct.pack('<I',bits))[0])
def counts(records):
 bins={(i,r):dict(states=0,positive_states=0,calls=0,positive_calls=0) for i in [0,1] for r in [0,1]}
 for (own,net,node),(ready,y,n) in records.items():
  b=bins[own,ready];b['states']+=1;b['positive_states']+=y;b['calls']+=n;b['positive_calls']+=n*y
 return bins
def fit(train,data):
 totals={(i,r):[0,0] for i in [0,1] for r in [0,1]}
 for case in train:
  for key,b in counts(data[case]).items():totals[key][0]+=b['states'];totals[key][1]+=b['positive_states']
 base={};full={};stats={};global_n=sum(x[0] for x in totals.values());global_p=sum(x[1] for x in totals.values())
 for i in [0,1]:
  n=sum(totals[i,r][0] for r in [0,1]);p=sum(totals[i,r][1] for r in [0,1]);q=Fraction(p+1,n+2) if n else Fraction(global_p+1,global_n+2);base[str(i)]=word(q)
  for r in [0,1]:
   nn,pp=totals[i,r];key=f'{i},{r}';full[key]=word(Fraction(pp+1,nn+2)) if nn else base[str(i)];stats[key]=dict(states=nn,positive_states=pp,backoff_to_I_only=nn==0)
 return dict(train_cases=sorted(train),I_only_words=base,I_ready_words=full,cell_counts=stats,training_state_count=global_n)
def score(cells,model,weight):
 total=0;values={k:Fraction(0) for k in ['zero','hard_ready','I_only','I_ready']};suffix='calls' if weight=='calls' else 'states';positive='positive_'+suffix
 for (i,r),b in cells.items():
  n=b[suffix];p=b[positive];total+=n;pred={'zero':Fraction(0),'hard_ready':Fraction(r),'I_only':ratio(model['I_only_words'][str(i)]),'I_ready':ratio(model['I_ready_words'][f'{i},{r}'])}
  for name,q in pred.items():values[name]+=p*(1-q)**2+(n-p)*q*q
 return dict(observations=total,Brier={name:float(value/total) for name,value in values.items()},exact_error_sums={name:[value.numerator,value.denominator] for name,value in values.items()})
def main():
 assert not D.exists();D.mkdir();vp=S/'verification.json';ind=S/'independent_verification_v1.json';source=json.loads(vp.read_text());bindings={str(p):sha(p) for p in [vp,ind,Path(__file__)]};protocol={'status':'FIXED_EXPECTED_MEAN_CALIBRATION_NOT_NATIVE_INJECTION','features':['current retained membership I, 0/1','bounded ready OTHER-NET forecast alarm, 0/1'],'fit':'Beta(1,1) posterior mean per I/ready cell. Train each distinct (I,NET,node) state once per case; no identifiers as features. Empty cell backs off to I-only, empty I to global prior. Quantize once to IEEE binary32 words. No parameter/threshold sweep.','controls':['same-fold I-only Beta(1,1) base-rate calibration','zero future-other mean','previous hard ready alarm'],'holdout':'Leave whole episode_01/02/03 group out including BOTH widths128/160. Four training cases, two test cases per fold. Development exposed; not strict unseen-family or global-forecast gate.','evaluation':'Exact binary32 probability Brier sums for call-multiplicity and equal (I,NET,node) state weighting, every heldout case reported. Splitting same NET/node across I states is explicit; no global occupancy-quality replacement.','admission':'Require casewise improvement over I-only control on both weightings to justify considering a native test; aggregate gain alone insufficient. Original full9 quality/native/fullpaid/unseen obligations unchanged.','bindings':dict(bindings)};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');data={};unavailable=[]
 for row in source['rows']:
  case=row['case']
  if not row['available']:unavailable.append(dict(case=case,reason=row['reason']));continue
  inp=Path(row['input_path']);assert sha(inp)==row['input_sha256'];lp=L/case/'capture/queries.tsv.ledger.bin';truth=final_inverse(lp);records={}
  for net,node,connection,own,ready,n in map(json.loads,inp.open()):
   y=int(bool(truth[node]-{net}));key=(own,net,node)
   if key in records:assert records[key][:2]==(ready,y);records[key]=(ready,y,records[key][2]+n)
   else:records[key]=(ready,y,n)
  data[case]=records;bindings[str(inp)]=sha(inp);bindings[str(lp)]=sha(lp)
 assert len(data)==6 and len(unavailable)==3;folds=[];rows=[]
 for group in ['episode_01','episode_02','episode_03']:
  test=sorted(x for x in data if x.split('/')[1]==group);train=sorted(set(data)-set(test));assert len(test)==2 and len(train)==4 and all(x.split('/')[1]!=group for x in train);model=fit(train,data);model['test_cases']=test;model['heldout_episode']=group;folds.append(model)
  for case in test:
   cells=counts(data[case]);calls=score(cells,model,'calls');states=score(cells,model,'states');rows.append(dict(case=case,heldout_episode=group,calls=calls,states=states,casewise_Brier_improves_I_only=calls['Brier']['I_ready']<calls['Brier']['I_only'] and states['Brier']['I_ready']<states['Brier']['I_only']));print('MEAN_CALIBRATION_CASE',case,json.dumps(dict(calls=calls['Brier'],states=states['Brier'])),flush=True)
 assert len(rows)==6 and all(sha(p)==h for p,h in bindings.items());(D/'models.json').write_text(json.dumps(dict(folds=folds,feature_fields=protocol['features']),indent=2)+'\n');(D/'verification.json').write_text(json.dumps(dict(status='GROUP_HELDOUT_EXPECTED_DEMAND_CALIBRATION_COMPLETE',rows=sorted(rows,key=lambda x:x['case']),unavailable=unavailable,bindings=bindings,models_sha256=sha(D/'models.json'),scope='No native injection, case/width disabling, unseen or original quality-gate claim.'),indent=2)+'\n')
if __name__=='__main__':main()
