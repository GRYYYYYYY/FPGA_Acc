"""Four pre-existing input classes; descriptive sign-error accounting only."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def sign(v):return '+' if v>0 else '-' if v<0 else '0'
def main():
 out=R/'experiments/mmc_owner_gain_sign_classes_v1_2026-10-19';out.mkdir(exist_ok=False);source=R/'experiments/mmc_owner_NET_gain_diagnosis_v1_2026-10-19/results.json';prior=read(source);fr=R/'experiments/mmc_label_free_NET_features_v1_2026-10-19';featureproof=read(fr/'receipt.json');bindings={str(p):sha(p) for p in [source,fr/'receipt.json',Path(__file__).resolve()]};rows=[]
 for old in prior['rows']:
  case=old['case'];fp=fr/(case+'.jsonl');assert featureproof['bindings'][str(fp)]==sha(fp);features={x['net_id']:x['values'] for x in map(json.loads,fp.open())};cp=R/f'experiments/mmc_owner_frequency_development_v1_2026-10-19/{case}/choices.jsonl';op=R/f'experiments/mmc_aggregate_L1_oracle_v1_2026-10-19/{case}/choices.jsonl';assert prior['bindings'][str(cp)]==sha(cp) and prior['bindings'][str(op)]==sha(op);choices={x['net_id']:x for x in map(json.loads,cp.open())};oracle={x['net_id']:x for x in map(json.loads,op.open())};assert set(choices)==set(oracle)==set(features) and len(choices)==55300
  groups=defaultdict(Counter);details=[]
  for n,c in choices.items():
   f=features[n];cls=('multi' if f[0]>1 else 'single')+'/'+('changed' if f[1]>0 else 'unchanged');w=oracle[n]['aggregate_gain'];pred=c['expected_gain_scaled'];selected=c['pick']=='B';opt=oracle[n]['pick']=='B'
   for cohort,include in [('all',True),('selected_positive',selected and pred>0),('oracle_only',opt and not selected),('model_only',selected and not opt)]:
    if not include:continue
    key=cohort+'|'+cls;g=groups[key];g['NETs']+=1;g['pred'+sign(pred)+'_true'+sign(w)]+=1;g['true_gain']+=w;g['true_benefit']+=max(0,w);g['true_harm']+=max(0,-w);g['predicted_gain_scaled']+=pred
   details.append((n,cls,pred,w,selected,opt))
  # Independently filter stored scalar rows and reconcile previous group totals.
  for cohort,oldkey in [('selected_positive','selected_positive_predicted'),('oracle_only','oracle_only'),('model_only','model_only')]:
   subset=[g for k,g in groups.items() if k.startswith(cohort+'|')];oldg=old['groups'][oldkey]
   for key in ['NETs','true_gain','true_benefit','true_harm','predicted_gain_scaled']:assert sum(g[key] for g in subset)==oldg[key]
  assert sum(g['NETs'] for k,g in groups.items() if k.startswith('all|'))==55300
  for key,g in groups.items():
   assert g['true_gain']==g['true_benefit']-g['true_harm'];assert sum(v for k,v in g.items() if k.startswith('pred') and k!='predicted_gain_scaled')==g['NETs']
  rows.append(dict(case=case,groups={k:dict(v) for k,v in sorted(groups.items())}));bindings.update({str(p):sha(p) for p in [fp,cp,op]});print(case,{k:dict(v) for k,v in groups.items() if k.startswith('selected_positive|')},flush=True)
 with (out/'results.json').open('x') as f:json.dump(dict(status='ALL3_FIXED_FOUR_CLASS_SIGN_TABLES_AND_PRIOR_GAIN_TOTALS_RECONCILED',rows=rows,bindings=bindings,scope='Descriptive exposed-data classes; no fitted model or score changes. Marginal class rates cannot justify accepting individual updates or relaxing capacity dependencies.'),f,indent=2)
if __name__=='__main__':main()
