"""Exposed-data descriptive ownership diagnostic; no fitted rule or policy selection."""
from pathlib import Path
import json,hashlib
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def snapshot(trace,target):
 phase=None;owners=None;observed=None;result={}
 with trace.open() as f:
  assert f.readline()=='TRACE 1\n'
  for line in f:
   if line.startswith('CP '):
    w=line.split();phase='first' if w[1]=='iteration_end_after_local_opins' and w[2]=='1' else 'final' if w[1]=='final_after_best_restore' else None
    if phase:owners=defaultdict(list);observed={}
   elif phase and line.startswith('T '):
    w=list(map(int,line.split()[1:]));net,ignored,present,remaining,count=w[:5];nodes=w[5:];assert len(nodes)==count and len(set(nodes))==count
    if not ignored and present:
     for node in target.intersection(nodes):owners[node].append(net)
   elif phase and line.startswith('V '):
    n,occ,cap=map(int,line.split()[1:]);assert occ>cap
    if n in target:assert n not in observed;observed[n]=(occ,cap)
   elif phase and line=='CE\n':
    assert phase not in result;result[phase]=({n:sorted(v) for n,v in owners.items()},observed);phase=None
 assert set(result)=={'first','final'}
 return result
def main():
 O=R/'experiments/mmc_preferred_resource_competition_diagnosis_v1_2026-10-19';O.mkdir(exist_ok=False)
 review=R/'experiments/mmc_preferred_NET_hint_study_closure_v1_2026-10-19/research_decision_v1.json';assert json.loads(review.read_text())['status']=='ALL3_PREFERRED_NET_HINT_NATIVE_COMPONENT_GATES_FAILED_NOT_PROMOTED'
 protocol={'scope':'Posthoc exposed MMC descriptive counts only, no causal claim, fitted weights, alternative owners or new native jobs. NET owner counts do not assume non-NET occupancy zero.','cases':['episode_01','episode_02','episode_03'],'arms':['zero','forecast','preferred'],'phases':['first','final'],'categories':['unused','preferred_only','preferred_with_competitors','other_only'],'selection':'Previously frozen claims; never reassigned from observed routes.'}
 (O/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');bindings={str(p):sha(p) for p in [review,Path(__file__).resolve(),O/'protocol.json']};rows=[]
 for case in protocol['cases']:
  claim=R/f'experiments/mmc_preferred_NET_claims_v1_2026-10-19/{case}/claims.jsonl';claims={x['node']:x for x in map(json.loads,claim.read_text().splitlines())};target=set(claims);bindings[str(claim)]=sha(claim)
  for arm in protocol['arms']:
   trace=R/(f'experiments/mmc_preferred_NET_native_utility_v1_2026-10-19/{case}/owner_trace.tsv' if arm=='preferred' else f'experiments/mmc_first_iteration_hint_utility_v1_2026-10-19/{case}/{arm}/cold/owner_trace.tsv');data=snapshot(trace,target);bindings[str(trace)]=sha(trace)
   for phase,(owners,observed) in data.items():
    categories=Counter();hist=Counter();ties=Counter();probone=Counter();totalpairs=0;fp=O/f'{case}_{arm}_{phase}.jsonl'
    with fp.open('x') as out:
     for n,c in sorted(claims.items()):
      actual=owners.get(n,[]);chosen=c['preferred_net'] in actual;category='unused' if not actual else 'preferred_only' if chosen and len(actual)==1 else 'preferred_with_competitors' if chosen else 'other_only';categories[category]+=1;hist[len(actual)]+=1;totalpairs+=len(actual)
      if c['max_probability_ties']>1:ties[category]+=1
      if c['probability']=='1':probone[category]+=1
      if n in observed:assert observed[n][1]==1 and observed[n][0]>=len(actual)
      out.write(json.dumps({'node':n,'preferred_NET':c['preferred_net'],'actual_NETs':actual,'category':category,'native_overuse_observation':observed.get(n)},separators=(',',':'))+'\n')
    assert sum(categories.values())==len(claims)==sum(hist.values());rows.append({'case':case,'arm':arm,'phase':phase,'resources':len(claims),'categories':dict(categories),'NET_owner_count_histogram':dict(hist),'total_NET_resource_pairs':totalpairs,'predicted_max_probability_ties_categories':dict(ties),'preferred_probability_one_categories':dict(probone),'native_observed_overused_resources':len(observed),'per_resource':str(fp)});bindings[str(fp)]=sha(fp);print('COMPETITION',case,arm,phase,dict(categories),flush=True)
 (O/'review.json').write_text(json.dumps({'status':'ALL9_ARM_PHASE_RESOURCE_COMPETITION_COUNTS_COMPLETE','rows':rows,'bindings':bindings,'scope':protocol['scope'],'independent_verification_pending':True},indent=2)+'\n')
if __name__=='__main__':main()
