"""Single untuned Bayes half decision for every frozen main/control26 output."""
import json,math
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_track_aware_cart_half_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);L=E/'wbuart_track_aware_cart_v1_2026-10-20';source=L/'predictions_frozen.json';proof=L/'independent_verification_v1.json';assert all(sha(p)==h for p,h in read(proof)['bindings'].items());v=read(source);files=[source,proof,Path(__file__),E/'binary_tie_rank_limits_contract_v1_2026-10-20/verification.json',E/'wbuart_prior_uncertainty_review_v1_2026-10-20/verification.json'];bindings={str(p):sha(p) for p in files};(D/'protocol.json').write_text(json.dumps({'policy':'One fixed decision q=1 iff frozen p>=0.5, else0, applied to all18 main/control26 predictions, same point counts for resource and summed original spatial bins. No threshold search, retraining, rounding variants or case selection.','scope':'Supplemental retrospective representation study, not a replacement of original CART soft-primary experiment. Generic hard/marginal representations were already explored on old MMC and are not claimed novel. Preserve both main/control26 and original source/H0 raw controls.','bindings':bindings},indent=2)+'\n');rows=[]
 for r in v['rows']:
  scores=read(r['probabilities']);assert all(math.isfinite(p) and 0<=p<=1 for p in scores);values=[int(p>=.5) for p in scores];out=D/r['case']/r['mode'];out.mkdir(parents=True);p=out/'point_counts.json';p.write_text(json.dumps(values,separators=(',',':'))+'\n');rows.append({**r,'point_counts':str(p)});bindings[str(p)]=sha(p);bindings[r['probabilities']]=sha(r['probabilities'])
 assert len(rows)==18
 (D/'predictions_frozen.json').write_text(json.dumps({'status':'ALL18_FIXED_HALF_DECISIONS_FROZEN_BEFORE_EVALUATION','rows':rows,'target_labels_read':False,'bindings':bindings},indent=2)+'\n');print('ALL18_CART_HALF_DECISIONS_FROZEN')
if __name__=='__main__':main()
