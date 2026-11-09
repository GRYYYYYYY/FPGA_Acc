"""Independent price oracle across source initialization, round updates, owner release."""
import sys,json,random,copy,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from source_native_history_input_v1 import initialize,normalize,load
from cached_multiplicative_occupancy_context_v1 import Context
from source_binding_v2 import closure
D=R/'experiments/source_history_lifecycle_contract_v1_2026-10-20'
class Search:
 def __init__(self,c,b):self.fields={'capacities':tuple(c)};self.base=tuple(b);self.closed=False
 def prepare(self,p,w,**kw):self.prices=dict(p);assert max(p.values())<=kw['price_ceiling']
 def patch_prices(self,p):self.prices.update(p)
def main():
 D.mkdir(exist_ok=False);rng=random.Random(20261020);checks=transactions=0;rejections=0
 for trial in range(120):
  n=12;m=8;caps=[rng.randrange(1,4) for _ in range(n)];base=[rng.randrange(1000) for _ in range(n)];spans={i:rng.randrange(5) for i in range(n) if rng.randrange(2)};prior={i:rng.randrange(1,17) for i in range(n) if rng.randrange(2)};before=copy.deepcopy((spans,prior));owners=[{net for net in range(m) if rng.randrange(3)==0} for _ in range(n)];encoded=initialize(spans,prior,n);s=Search(caps,base);context=Context(s,caps,base,m,spans);added=Counter()
  assert initialize(spans,{},n)==Counter(spans)
  for round_index in range(2):
   changed={i:len(v)-caps[i] for i,v in enumerate(owners) if len(v)>caps[i]}
   if round_index>0:encoded.update(changed);added.update(changed)
   assert all(encoded[i]-spans.get(i,0)==prior.get(i,0)+added[i] for i in range(n));context.start_round(encoded,7,{i:len(v) for i,v in enumerate(owners)})
   for _ in range(20):
    net=rng.randrange(m);old={i for i,v in enumerate(owners) if net in v};view=context.begin(old)
    for i in range(n):
     other=len(owners[i]-{net});expected=base[i]*(1+prior.get(i,0)+added[i])*(1+max(0,other-caps[i]+1))+7*spans.get(i,0);assert base[i]+view.get(i)==base[i]+s.prices[i]==expected;checks+=1
    new={i for i in range(n) if rng.randrange(3)==0}
    for i in old-new:owners[i].remove(net)
    for i in new-old:owners[i].add(net)
    context.finish({i:len(owners[i]) for i in old^new});transactions+=1
    try:view.get(0)
    except RuntimeError:pass
    else:raise AssertionError('stale snapshot')
   assert (spans,prior)==before
 for bad in [{'01':2},{0:True},{-1:1},{12:1},{'0':1,0:1},{0:-1}]:
  try:normalize(bad,12,'fixture')
  except ValueError:rejections+=1
  else:raise AssertionError('domain accepted')
 P=R/'experiments/source_native_history_prior_v1_2026-10-20/prior.json';p=json.loads(P.read_text());h,bindings=load(P,p['graph_sha256'],p['source_route_sha256'],p['nodes']);assert len(h)==34948 and max(h.values())==16
 for graph,route in [('0'*64,p['source_route_sha256']),(p['graph_sha256'],'0'*64)]:
  try:load(P,graph,route,p['nodes'])
  except ValueError:rejections+=1
  else:raise AssertionError('epoch accepted')
 bindings.update(closure([Path(__file__)]));(D/'verification.json').write_text(json.dumps(dict(status='SOURCE_PRIOR_ONCE_SPAN_SEPARATION_ROUND_UPDATES_OWNER_PRICE_CONTRACT_PASS',random_graphs=120,transactions=transactions,node_price_checks=checks,invalid_domains_and_epochs_rejected=rejections,empty_prior_reproduces_old_initialization=True,bindings=bindings,scope='Mock search pricing transaction contract and real prior authenticated load only; no full predictor/native utility/quality admission.'),indent=2)+'\n');print('PASS',transactions,checks,rejections)
if __name__=='__main__':main()
