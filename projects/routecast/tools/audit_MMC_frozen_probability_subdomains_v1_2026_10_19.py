"""Posthoc calibration accounting in fixed input-defined domains; never refits p."""
import json,array,hashlib
from pathlib import Path
from collections import Counter
from fractions import Fraction
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def arr(p,t):
 a=array.array(t);a.frombytes(p.read_bytes());return a

def main():
 out=R/'experiments/mmc_frozen_probability_subdomains_v1_2026-10-19';out.mkdir(exist_ok=False)
 cp=R/'experiments/mmc_resource_context_v1_2026-10-19/CHANNEL_ids.u32';ids=arr(cp,'I');master=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=read(master);bindings={str(p):sha(p) for p in [cp,master,Path(__file__).resolve()]};rows=[]
 for item in plan['cases']:
  case=item['case'];bp=R/f'experiments/mmc_candidate_ownership_implications_v1_2026-10-19/{case}/banks.jsonl';mp=R/f'experiments/mmc_resource_probability_development_v1_2026-10-19/{case}/history_A_B_prefix_direction_segment/model.json';pp=mp.with_name('probabilities.u32');ctx=R/f'experiments/mmc_resource_context_v1_2026-10-19/{case}.u16';tp=Path(item['native_label']);assert sha(tp)==plan['bindings'][str(tp)]
  model=read(mp);assert case==model['evaluation_case'] and case not in model['training_cases'];scale=model['scale'];probs=arr(pp,'I');codes=arr(ctx,'H');assert len(ids)==len(probs)==len(codes)==258720
  variable=set();owned=set()
  for line in bp.open():
   b= json.loads(line);a=set(b['A']);bb=set(b['B']);variable.update(a^bb);owned.update(a)
  truth={int(n):v for n,v in read(tp)['node_occupancy'].items()};hist={g:Counter() for g in ['fixed_unowned','fixed_owned','variable']};direct=Counter();sq=Counter();ns=Counter();occ=Counter()
  for n,c,p in zip(ids,codes,probs):
   assert p==model['probability_int'][c];t=truth.get(n,0);assert t in (0,1);g='variable' if n in variable else 'fixed_owned' if n in owned else 'fixed_unowned';hist[g][c,t]+=1;direct[g]+=(p-scale*t)**2;sq[g]+=p;ns[g]+=1;occ[g]+=t
  groups={}
  for g,h in hist.items():
   check=sum(count*(model['probability_int'][c]-scale*t)**2 for (c,t),count in h.items());assert check==direct[g]
   calibration=Fraction(0);within=Fraction(0);absolute=Fraction(0);cats=[]
   for c in range(216):
    n=h[c,0]+h[c,1]
    if not n:continue
    s=h[c,1];p=Fraction(model['probability_int'][c],scale);rate=Fraction(s,n);calibration+=n*(p-rate)**2;within+=n*rate*(1-rate);absolute+=n*abs(p-rate);cats.append(dict(category=c,resources=n,occupied=s,frozen_probability_int=model['probability_int'][c]))
   assert calibration+within==Fraction(direct[g],scale**2)
   groups[g]=dict(resources=ns[g],occupied=occ[g],mean_probability=float(Fraction(sq[g],ns[g]*scale)),occupancy_rate=occ[g]/ns[g],Brier=float(Fraction(direct[g],ns[g]*scale**2)),category_calibration_component=float(calibration/ns[g]),within_category_component=float(within/ns[g]),category_ECE=float(absolute/ns[g]),exact_Brier_sum=str(Fraction(direct[g],scale**2)),categories=cats)
  assert sum(ns.values())==258720
  row=dict(case=case,groups=groups,full_Brier=float(Fraction(sum(direct.values()),258720*scale**2)));rows.append(row);bindings.update({str(p):sha(p) for p in [bp,mp,pp,ctx,tp]});print(case,{g:{k:v for k,v in z.items() if k in ['Brier','category_calibration_component','within_category_component','category_ECE']} for g,z in groups.items()},flush=True)
 (out/'results.json').write_text(json.dumps(dict(status='ALL3_FROZEN_PROBABILITIES_DIRECT_HISTOGRAM_AND_EXACT_CALIBRATION_DECOMPOSITIONS_VERIFIED',rows=rows,bindings=bindings,scope='Posthoc descriptive categories only; same216 input categories and unchanged frozen probabilities. Empirical category rate uses evaluation truth only as diagnostic, never as a deployed probability or fitted replacement. Brier decomposition does not certify rank gates or native utility.'),indent=2)+'\n')
if __name__=='__main__':main()
