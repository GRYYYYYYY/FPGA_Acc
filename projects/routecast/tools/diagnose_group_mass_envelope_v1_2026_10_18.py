"""Optimistic six-source convex-envelope mass lower bound; no target fitting."""
import sys,json
from pathlib import Path
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 src=R/'experiments/mmc_anchored_NET_forecasts_v1_2026-10-18';pp=src/'protocol.json';plan=json.loads(pp.read_text());sp=R/'experiments/mmc_anchored_NET_forecasts_verification_v1_2026-10-18/verification.json';proof=json.loads(sp.read_text());gp=R/'experiments/mmc_typed_collision_risk_v1_2026-10-18/groups.json';groups=json.loads(gp.read_text());channelgroups={i:g for i,g in enumerate(groups['groups']) if g['kind']=='geometry_channel'};out=R/'experiments/mmc_group_mass_envelope_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [Path(__file__),pp,sp,gp]};rows=[];details={}
 for case in plan['cases']:
  vp=R/f'experiments/mmc_multiplacement_quality_v1_2026-10-18/{case}/vectors.json';vproof=json.loads(vp.with_name('verification.json').read_text());assert sha(vp)==vproof['bindings'][str(vp)];truth={r['node']:r['labels']['cold'] for r in json.loads(vp.read_text())['channels']};assert len(truth)==258720 and all(x in [0,1] for x in truth.values());bindings[str(vp)]=sha(vp);bindings[str(vp.with_name('verification.json'))]=sha(vp.with_name('verification.json'));sources={}
  for method in plan['sources']:
   p=src/(case+'__'+method+'.json');assert sha(p)==proof['bindings'][str(p)];bindings[str(p)]=sha(p);journal=json.loads(p.read_text())['group_totals'];sources[method]={gid:Fraction(journal.get(str(gid),{}).get('expected_occupancy_total','0')) for gid in channelgroups};assert all(x.denominator==1 for x in sources[method].values())
  lower=0;below=above=inside=0;records=[];single={s:0 for s in sources}
  for gid,g in channelgroups.items():
   masses=[v[gid] for v in sources.values()];low,high=min(masses),max(masses);target=sum(truth[n] for n in g['members']);distance=max(low-target,target-high,0);lower+=distance;below+=target<low;above+=target>high;inside+=low<=target<=high
   for s in single:single[s]+=abs(sources[s][gid]-target)
   records.append(dict(group=gid,minimum_source_mass=int(low),maximum_source_mass=int(high),cold_mass=target,envelope_distance=int(distance)))
  assert lower<=min(single.values());details[case]=records;rows.append(dict(case=case,groups=len(channelgroups),cold_below_all_sources=below,cold_above_all_sources=above,cold_inside_source_range=inside,optimistic_mixture_L1_floor=int(lower),optimistic_mixture_MAE_floor=float(lower/258720),best_single_source_group_L1_floor=int(min(single.values())),single_source_group_floors={s:int(x) for s,x in single.items()}))
 for p,h in bindings.items():assert sha(p)==h
 (out/'group_intervals.json').write_text(json.dumps(details,separators=(',',':')))
 with (out/'diagnosis.json').open('x') as f:json.dump(dict(status='six_source_convex_group_mass_envelopes_computed',bindings=bindings,group_intervals_sha256=sha(out/'group_intervals.json'),rows=rows,proof='Any convex combination of source group masses lies in[min,max]. Triangle inequality gives node L1 >= sum_group distance(cold_group_mass,[min,max]). Allowing independent weights per group is an optimistic relaxation of one global mixture; floor need not be attainable by legal routes or shared weights.',scope='Retrospective exposed cold targets; no mixture weights fitted, no primary/gate replacement, new forecast, native routing or causal/unseen claim.'),f,indent=2)
 print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
