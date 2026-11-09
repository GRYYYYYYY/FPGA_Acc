"""Exact error support decomposition after fixed candidate quality verification."""
import collections,json,sys
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';root=E/'mmc_owner_expansion_quality_v1_2026-10-18';out=E/'mmc_owner_expansion_residual_support_v1_2026-10-18';assert (root/'results.json').exists();out.mkdir(exist_ok=False);bindings=closure([Path(__file__)]);rows=[]
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 def admit(p):
  v=load(p);assert all(sha(k)==h for k,h in v['bindings'].items());bindings.update(v['bindings']);return v
 allcases=admit(root/'results.json')
 for case in ['case_01','case_02','case_03']:
  proof=admit(root/case/'verification.json');assert proof['status']=='pass' and proof['histogram_rank_topk_mae_checks']==12;vectors=load(root/case/'vectors.json');comparison=admit(root/case/'comparison.json')
  for domain,scope in [('channels','concrete'),('bins','spatial')]:
   table=vectors[domain];n=len(table)
   for control in ['native_retained_on','previous_native']:
    hist={k:collections.Counter() for k in ['new_changed','old_changed','unchanged','new_total','old_total']};changed=0;improved=0;worsened=0;equal_error=0
    for cell in table:
     cap=cell['capacity'];new=cell['predictions']['owner_expansion_on'];old=cell['predictions'][control];truth=cell['labels']['cold'];a=abs(new-truth);b=abs(old-truth);hist['new_total'][cap]+=a;hist['old_total'][cap]+=b
     if new!=old:
      changed+=1;hist['new_changed'][cap]+=a;hist['old_changed'][cap]+=b;improved+=a<b;worsened+=a>b;equal_error+=a==b
     else:hist['unchanged'][cap]+=a
    exact={k:sum((F(v,c) for c,v in h.items()),F(0))/n for k,h in hist.items()};assert exact['new_total']==exact['new_changed']+exact['unchanged'] and exact['old_total']==exact['old_changed']+exact['unchanged'];delta=exact['new_total']-exact['old_total'];assert delta==exact['new_changed']-exact['old_changed'];assert improved+worsened+equal_error==changed
    assert abs(float(exact['new_total'])-comparison['metrics']['cold']['owner_expansion_on'][scope]['mae'])<1e-12;assert abs(float(exact['old_total'])-comparison['metrics']['cold'][control][scope]['mae'])<1e-12
    # Alternative integer common-denominator reduction checks every exact total.
    import math
    denom=math.lcm(*(cell['capacity'] for cell in table));direct_new=sum(abs(c['predictions']['owner_expansion_on']-c['labels']['cold'])*(denom//c['capacity']) for c in table);direct_old=sum(abs(c['predictions'][control]-c['labels']['cold'])*(denom//c['capacity']) for c in table);assert F(direct_new,n*denom)==exact['new_total'] and F(direct_old,n*denom)==exact['old_total']
    rows.append(dict(case=case,domain=domain,control=control,coordinates=n,changed_coordinates=changed,unchanged_coordinates=n-changed,changed_improved=improved,changed_worsened=worsened,changed_equal_absolute_error=equal_error,normalized_MAE_exact={k:str(v) for k,v in exact.items()},normalized_MAE={k:float(v) for k,v in exact.items()},normalized_MAE_delta=float(delta),unchanged_share_of_candidate_MAE=float(exact['unchanged']/exact['new_total']) if exact['new_total'] else None,original_cold_primary_gate_pass=proof['primary_gate_pass']))
 assert all(sha(k)==h for k,h in bindings.items())
 (out/'results.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,status='all12_exact_support_decompositions_and_integer_common_denominator_reductions_match_verified_quality_MAE',scope='Descriptive residual support of the fixed owner-expanded point forecast versus original local and previous-native forecasts. Unchanged numeric coordinates are not a lower bound for a different future algorithm. No rank impossibility theorem, causal attribution, threshold tuning, new native utility or complete workflow speed claim.'),indent=2));print(json.dumps(rows),flush=True)
if __name__=='__main__':main()
