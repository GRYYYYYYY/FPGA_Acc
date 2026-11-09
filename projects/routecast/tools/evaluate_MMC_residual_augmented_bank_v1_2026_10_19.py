"""Frozen original/one-node/residual tree banks; physical vs fixed-budget gates."""
import pathlib,json,itertools,hashlib,xml.etree.ElementTree as ET
from collections import Counter
from coupled_NET_tree_candidates_v1 import select
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_residual_augmented_bank_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O.mkdir(exist_ok=False);A=R/'experiments/mmc_complete_tree_bank_csr_v2_2026-10-19';B=R/'experiments/mmc_residual_capacity_group_v1_2026-10-19';proofs=[A/'independent_XML_verification_v1.json',B/'independent_verification_v1.json'];bindings={str(p):sha(p) for p in proofs};bv=json.loads(proofs[1].read_text());assert bv['all_five_capacity_legal'];graph=next(pathlib.Path(p) for p in bv['bindings'] if p.endswith('rr_graph.xml'));assert sha(graph)==bv['bindings'][str(graph)];caps={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':caps[int(e.get('id'))]=int(e.get('capacity'));stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 nets=[1395,1400,1404,1754,2925];banks={};strict={};violations={};references={}
 for net in nets:
  banks[net]=[];strict[net]=[];references[net]=[];base=json.loads((A/f'net_{net}_original.json').read_text());budgets=base['sink_budgets'];violations[net]=[]
  for p in [A/f'net_{net}_original.json',A/f'net_{net}_blocked.json',B/f'net_{net}_tree.json']:
   proof=json.loads(proofs[0 if p.parent==A else 1].read_text());assert sha(p)==proof['bindings'][str(p)];bindings[str(p)]=sha(p);tree=json.loads(p.read_text());costs=tree.get('sink_costs') or {s:lab[0] for s,lab in tree['sink_labels'].items()};bad=sum(costs[s]>budgets[s] for s in costs);violations[net].append(bad);candidate=dict(nodes=frozenset(tree['unique_nodes']),excess=tree['excess']);banks[net].append(candidate);references[net].append(str(p))
   if bad==0:strict[net].append(candidate)
 diagnostic=select(banks,caps,max_states=100000);fixed=select(strict,caps,max_states=100000);feasible=[]
 for mask in itertools.product(range(3),repeat=5):
  counts=Counter();total=0
  for net,ci in zip(nets,mask):counts.update(banks[net][ci]['nodes']);total+=banks[net][ci]['excess']
  if all(count<=caps[node] for node,count in counts.items()):feasible.append((total,mask))
 assert diagnostic['status']==('OPTIMAL_WITHIN_CANDIDATES' if feasible else 'INFEASIBLE_WITHIN_CANDIDATES');assert diagnostic['excess']==(min(c for c,_ in feasible) if feasible else None)
 if diagnostic['selection'] is not None:
  choice=diagnostic['selection'];assert tuple(choice[n] for n in nets) in [m for _,m in feasible]
 assert fixed['status']=='INFEASIBLE_WITHIN_CANDIDATES'
 bindings.update({str(graph):sha(graph),str(pathlib.Path(__file__).resolve()):sha(pathlib.Path(__file__).resolve()),str(R/'tools/coupled_NET_tree_candidates_v1.py'):sha(R/'tools/coupled_NET_tree_candidates_v1.py')})
 result=dict(status='243_DIAGNOSTIC_COMPLETE_TREE_COMBINATIONS_INDEPENDENTLY_ENUMERATED',references=references,original_budget_violations_by_candidate=violations,diagnostic_selection=diagnostic,original_budget_selection=fixed,feasible_diagnostic_combinations=len(feasible),independent_bruteforce_minimum_excess=min(c for c,_ in feasible) if feasible else None,bindings=bindings,scope='Five known MMC NETs, zero external occupancy, finite three-origin banks retaining duplicate candidates. Diagnostic physical capacity feasibility with reported RC relaxation is not accepted original RC budget feasibility, global optimum, full MMC route or native utility.')
 (O/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(diagnostic,flush=True);print('feasible',len(feasible),'original budgets',fixed['status'],flush=True)
if __name__=='__main__':main()
