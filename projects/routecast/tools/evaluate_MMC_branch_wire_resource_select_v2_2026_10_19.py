"""Prior/native pilot tree bank with resource-first selection and full old residual."""
import pathlib,json,hashlib,itertools,xml.etree.ElementTree as ET
from collections import Counter
from coupled_NET_tree_resource_select_v2 import select
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_branch_wire_resource_select_v2_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O.mkdir(exist_ok=False);A=R/'experiments/mmc_prior_native_budget_bank_v1_2026-10-19';B=R/'experiments/mmc_prior_budget_branch_wire_pilot_v1_2026-10-19';vp=B/'independent_verification_v1.json';v=json.loads(vp.read_text());assert v['status']=='FULL115572_CONNECTION_XML_RC_CAPACITY_AND_ALL80_RESOURCE_TRANSACTIONS_PASS';ap=A/'independent_verification_v1.json';av=json.loads(ap.read_text());core=R/'experiments/coupled_NET_tree_resource_select_core_v2_2026-10-19/verification.json';assert json.loads(core.read_text())['status']=='LEX_UNIQUE_NET_RESOURCE_AND_RC_SELECTION_EXACT_CARTESIAN_PASS';spanp=B/'candidate_CHAN_spans.json';assert sha(spanp)==v['bindings'][str(spanp)];spans={int(n):w for n,w in json.loads(spanp.read_text()).items()};fp=A/'fixed_prior_other_NET_occupancy.json';assert sha(fp)==av['bindings'][str(fp)];fixed={int(n):w for n,w in json.loads(fp.read_text()).items()};graph=next(pathlib.Path(p) for p in v['bindings'] if p.endswith('rr_graph.xml'));assert sha(graph)==v['bindings'][str(graph)];caps={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':caps[int(e.get('id'))]=int(e.get('capacity'));stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 nets=[1395,1400,1404,1754,2925];banks={};refs={};bindings={str(p):sha(p) for p in [vp,ap,core,spanp,fp,graph,pathlib.Path(__file__).resolve(),R/'tools/coupled_NET_tree_resource_select_v2.py']}
 for n in nets:
  old=A/f'net_{n}_prior_native.json';new=B/f'net_{n}_tree.json';assert sha(old)==av['bindings'][str(old)] and sha(new)==v['bindings'][str(new)];base=json.loads(old.read_text());banks[n]=[];refs[n]=[str(old),str(new)]
  for path in [old,new]:
   x=json.loads(path.read_text());assert x['sink_costs'].keys()==base['sink_budgets'].keys();assert all(c<=base['sink_budgets'][s] for s,c in x['sink_costs'].items());cost=sum(c-base['sink_floors'][s] for s,c in x['sink_costs'].items());banks[n].append(dict(nodes=frozenset(x['unique_nodes']),excess=cost));bindings[str(path)]=sha(path)
 answer=select(banks,caps,spans,fixed,max_states=100000);feasible=[]
 for mask in itertools.product([0,1],repeat=5):
  occupancy=Counter();wire=0;rc=0
  for n,ci in zip(nets,mask):
   c=banks[n][ci];occupancy.update(c['nodes']);wire+=sum(spans.get(v,0) for v in c['nodes']);rc+=c['excess']
  if all(count+fixed.get(node,0)<=caps[node] for node,count in occupancy.items()):feasible.append(((wire,rc),mask))
 assert answer['status']=='OPTIMAL_WITHIN_CANDIDATES' and answer['objective']==min(c for c,_ in feasible);assert (answer['objective'],tuple(answer['selection'][n] for n in nets)) in feasible
 baseline=(sum(sum(spans.get(v,0) for v in banks[n][0]['nodes']) for n in nets),sum(banks[n][0]['excess'] for n in nets));assert answer['objective']<=baseline
 with (O/'verification.json').open('x') as f:json.dump(dict(status='REAL_MMC_FINITE_RESOURCE_FIRST_SELECTION_AND_ALL32_ORACLE_PASS',answer=answer,baseline_objective=baseline,feasible_combinations=len(feasible),candidate_references=refs,bindings=bindings,scope='Exact finite old-native/pilot complete-tree bank under full old-source external occupancy. Prior RC budget and capacity constraints hold. Not full new placement, native FULL/STA, original predictor-quality pass, unseen-family or end-to-end gain.'),f,indent=2)
 print(answer,'baseline',baseline,'feasible',len(feasible),flush=True)
if __name__=='__main__':main()
