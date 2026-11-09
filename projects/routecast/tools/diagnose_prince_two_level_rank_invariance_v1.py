"""Illustrative I=0 global extrapolation adds no ranking information; not a valid global head."""
import json,struct
from fractions import Fraction
from collections import defaultdict,Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_input_mean_trial_v1_2026-10-20'
def number(w):return Fraction(struct.unpack('<f',struct.pack('<I',w))[0])
def main():
 mp=E/'prince_sparse_other_mean_calibration_v1_2026-10-20/models.json';models=json.loads(mp.read_text());source=E/'prince_capacity_projection_v1_2026-10-20/verification.json';quality=E/'prince_capacity_projection_quality_v1_2026-10-20/verification.json';v=json.loads(source.read_text());old={x['case']:x for x in json.loads(quality.read_text())['rows']};bindings={str(p):sha(p) for p in [mp,source,quality,Path(__file__)]};rows=[]
 for row in v['rows']:
  if row['status']!='SCORES_READY':continue
  case=row['case'];proof=Path(row['verification']);assert sha(proof)==row['sha256'];p=json.loads(proof.read_text());scores=Path(p['score_file']);resources=E/'prince_quality_domains_v1_2026-10-20'/case.split('/')[0]/'resources.jsonl';bins=resources.parent/'spatial_bins.json';domain=list(map(json.loads,resources.open()));spatial=json.loads(bins.read_text());binary={x['id']:x['forecast_count'] for x in map(json.loads,scores.open())};assert set(binary)=={x['id'] for x in domain} and set(binary.values())<={0,1};model=next(x for x in models['folds'] if x['heldout_episode']==case.split('/')[1]);q0=number(model['I_ready_words']['0,0']);q1=number(model['I_ready_words']['0,1']);assert 0<q0<q1<1;pred={n:q0+(q1-q0)*b for n,b in binary.items()};assert sorted(binary,key=lambda n:(-binary[n],n))==sorted(pred,key=lambda n:(-pred[n],n));mass=Counter();baseline=Counter();estimated=defaultdict(Fraction)
  for node in domain:
   assert node['capacity']==1
   for key in node['bins']:key=tuple(key);mass[key]+=1;baseline[key]+=binary[node['id']];estimated[key]+=pred[node['id']]
  a={};b={}
  for bin in spatial:
   key=tuple(bin['key']);cap=bin['capacity'];assert mass[key]==cap;a[key]=Fraction(baseline[key],cap);b[key]=estimated[key]/cap;assert b[key]==q0+(q1-q0)*a[key]
  assert sorted(a,key=lambda k:(-a[k],k))==sorted(b,key=lambda k:(-b[k],k));rows.append(dict(case=case,resources=len(binary),spatial_bins=len(a),resource_order_and_ties_same=True,spatial_order_and_ties_same=True,affine_parameters=[[q0.numerator,q0.denominator],[q1.numerator,q1.denominator]],inherited_clipped_ready_primary_gate=old[case]['pass_both_controls']))
  for path in [proof,scores,resources,bins]:bindings[str(path)]=sha(path)
 assert len(rows)==6 and all(sha(p)==h for p,h in bindings.items());out=D/'illustrative_global_rank_invariance_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='NAIVE_TWO_LEVEL_GLOBAL_EXTRAPOLATION_RANKS_UNCHANGED',rows=rows,bindings=bindings,scope='Not an admitted global forecast: query mean learned only on eligible O=I states, so full-domain I=0 extension is out of domain. If naively extended, it is exactly q0+(q1-q0)*binary-ready occupancy. Both original resource and capacity-normalized spatial score orders/ties, hence all four ranking metrics and gates, remain identical to clipped ready baseline. Does not rule out other richer inputs or separately trained full-domain heads.'),indent=2)+'\n');print('TWO_LEVEL_GLOBAL_RANK_INVARIANCE',len(rows),sum(x['inherited_clipped_ready_primary_gate'] for x in rows))
if __name__=='__main__':main()
