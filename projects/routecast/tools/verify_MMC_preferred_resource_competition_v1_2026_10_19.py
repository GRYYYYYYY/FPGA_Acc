"""Independent first-iteration E records and final .route owner comparisons."""
from pathlib import Path
import json,re,hashlib
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_preferred_resource_competition_diagnosis_v1_2026-10-19';review=O/'review.json';d=json.loads(review.read_text());bindings={str(review):sha(review),str(Path(__file__).resolve()):sha(__file__)};results=[]
 for case in ['episode_01','episode_02','episode_03']:
  claim=R/f'experiments/mmc_preferred_NET_claims_v1_2026-10-19/{case}/claims.jsonl';claims={x['node']:x for x in map(json.loads,claim.read_text().splitlines())};target=set(claims);ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json';meta=json.loads(ep.read_text());names={name:int(n) for n,name in meta['net_names'].items()}
  for arm in ['zero','forecast','preferred']:
   base=R/(f'experiments/mmc_preferred_NET_native_utility_v1_2026-10-19/{case}' if arm=='preferred' else f'experiments/mmc_first_iteration_hint_utility_v1_2026-10-19/{case}/{arm}/cold');trace=base/'owner_trace.tsv';first=defaultdict(set);seen=set()
   with trace.open() as f:
    for line in f:
     if line.startswith('CP routed_before_local_opins 1'):break
     if not line.startswith('E '):continue
     event,iteration,net=map(int,line.split()[1:]);assert iteration==1 and net not in seen;seen.add(net);w=list(map(int,next(f).split()[1:]));assert w[0]==net and w[1:4]==[0,1,0] and w[4]==len(w[5:]);assert next(f)=='EE\n'
     for node in set(w[5:])&target:first[node].add(net)
   assert len(seen)==55300
   final=defaultdict(set);route=base/'output.route';current=None
   for line in route.open():
    if line.startswith('Net '):
     match=re.match(r'^Net \d+ \((.*)\)\s*$',line);current=names[match[1]] if match else None
    elif line.lstrip().startswith('Node:') and current is not None:
     node=int(line.split()[1])
     if node in target:final[node].add(current)
   for phase,actual in [('first',first),('final',final)]:
    row=next(x for x in d['rows'] if x['case']==case and x['arm']==arm and x['phase']==phase);fp=Path(row['per_resource']);entries=[json.loads(l) for l in fp.open()];assert [x['node'] for x in entries]==sorted(target);categories=Counter();hist=Counter()
    for x in entries:
     node=x['node'];owners=sorted(actual[node]);assert x['actual_NETs']==owners and x['preferred_NET']==claims[node]['preferred_net'];chosen=x['preferred_NET'] in owners;cat='unused' if not owners else 'preferred_only' if chosen and len(owners)==1 else 'preferred_with_competitors' if chosen else 'other_only';assert cat==x['category'];categories[cat]+=1;hist[len(owners)]+=1
    assert dict(categories)==row['categories'] and {str(k):v for k,v in hist.items()}==row['NET_owner_count_histogram'];results.append({'case':case,'arm':arm,'phase':phase,'exact_resource_owner_sets':len(entries),'independent_source':'native first E records' if phase=='first' else 'final physical .route'});bindings[str(fp)]=sha(fp)
   for f in [claim,ep,trace,route]:bindings[str(f)]=sha(f)
   print('INDEPENDENT_COMPETITION_PASS',case,arm,flush=True)
 (O/'independent_verification_v1.json').open('x').write(json.dumps({'status':'ALL18_RESOURCE_OWNER_SETS_AND_CATEGORIES_INDEPENDENTLY_VERIFIED','rows':results,'bindings':bindings,'scope':'NET owner sets/category arithmetic; native V occupancy observations remain covered by original independent owner replay, not assumed zero. No causal or unseen prediction claim.'},indent=2)+'\n')
if __name__=='__main__':main()
