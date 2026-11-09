"""Training split usage only; feature gain is not a causal utility claim."""
import json
from pathlib import Path
from fractions import Fraction as F
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_track_aware_cart_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=D/'independent_verification_v1.json';assert all(sha(p)==h for p,h in read(proof)['bindings'].items());rows=[];bindings={str(proof):sha(proof),str(Path(__file__)):sha(__file__)}
 for ep in ['episode_01','episode_02','episode_03']:
  p=D/ep/'main/model.json';m=read(p);nodes=m['nodes'];counts=[0]*31;gains=[F(0)]*31;N=nodes[0]['rows']
  for node in nodes:
   f=node['feature']
   if f<0:continue
   a,b=nodes[node['left']],nodes[node['right']];gain=2*(F(a['positive']**2,a['rows'])+F(b['positive']**2,b['rows'])-F(node['positive']**2,node['rows']))/N;assert gain>0;gains[f]+=gain;counts[f]+=1
  rows.append({'episode':ep,'architecture_split_count':sum(counts[26:]),'total_split_count':sum(counts),'architecture_gain_fraction':float(sum(gains[26:])/sum(gains)),'columns':[{'name':name,'splits':n,'normalized_training_gini_gain':str(gain)} for name,n,gain in zip(m['columns'],counts,gains)]});bindings[str(p)]=sha(p)
 out=D/'training_split_usage_v1.json';out.write_text(json.dumps({'status':'TRAINING_SPLIT_USAGE_RECONCILED','rows':rows,'bindings':bindings,'scope':'Describes frozen training trees only. Gain/usage does not imply causal benefit or heldout quality.'},indent=2)+'\n');print('TRACK_TRAINING_SPLITS_RECORDED')
if __name__=='__main__':main()
