"""Target-free grouping of archived rejected candidates, no commits or label reads."""
import json,sys,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from fractions import Fraction
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from zero_rc_budget_certificate_graph_v1 import load_graph
from diagnose_target_channel_release_dependencies_v2 import scc
E=R/'experiments';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';P=E/'prospective_external_family_fixed_nominal_pair_exchange_v1_2026-10-19';D=E/'prospective_external_family_rejected_candidate_groups_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 prior=read(P/'diagnosis.json');assert all(sha(k)==h for k,h in prior['bindings'].items());cases=read(A/'protocol.json')['cases'];graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);g=load_graph(graph);spans={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes' and e.get('type') in ('CHANX','CHANY'):
   loc=e.find('loc');n=int(e.get('id'));assert g['caps'][n]==1;spans[n]=1+max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 D.mkdir(exist_ok=False);bindings={str(P/'diagnosis.json'):sha(P/'diagnosis.json'),str(graph):sha(graph),str(Path(__file__).resolve()):sha(__file__),str(R/'tools/diagnose_target_channel_release_dependencies_v2.py'):sha(R/'tools/diagnose_target_channel_release_dependencies_v2.py')};(D/'protocol.json').write_text(json.dumps(dict(cases=[c['case'] for c in cases],policy='No target paths/labels read. Exact prior positive-overflow rebased candidate pool. Evaluate all nontrivial SCCs, dependency closures of every SCC, and full pool at same final ledger/history/round1 criticality. Common group-owner-excluded cost uses original perNET weighted raw+max-user congestion summed over group. This is a proposed batch diagnostic, not the original singleNET admission or actual commits.'),indent=2)+'\n');rows=[]
 def support(recs):
  ns=set()
  for q in recs:
   u=q['source'];ns.add(u);value=0;seen={u}
   for eid in q['answer']['physical_edge_ids']:
    assert g['us'][eid]==u;u=g['vs'][eid];assert u not in seen;seen.add(u);ns.add(u);value+=g['weights'][g['switches'][eid]]
   assert u==q['sink'] and value==q['answer']['delay']<=q['budget_integer']
  return ns
 for c in cases:
  case=c['case'];folder=A/case/'native_retained/warm_timing_round_updated';state=read(folder/'round1.json');receipt=read(folder/'receipt.json');old=defaultdict(list)
  for q in state['records']:old[q['net_id']].append(q)
  oldsets={n:support(qs) for n,qs in old.items()};ledger={int(n):v for n,v in state['ledger'].items()};assert dict(Counter(u for ns in oldsets.values() for u in ns))==ledger;owners=defaultdict(set)
  for n,ns in oldsets.items():
   for u in ns:owners[u].add(n)
  def pressure(delta):
   assert all(ledger.get(u,0)+d>=0 for u,d in delta.items());return sum(max(0,ledger.get(u,0)+d-g['caps'][u])-max(0,ledger.get(u,0)-g['caps'][u]) for u,d in delta.items())
  pool={};newsets={}
  for event in receipt['rounds'][1]['events']:
   if 'rejected_records' not in event or event['prospective_overflow_delta']<=0:continue
   n=event['net_id'];qs=event['rejected_records'];assert {q['connection_id'] for q in qs}=={q['connection_id'] for q in old[n]};a={q['connection_id']:{k:v for k,v in q.items() if k!='answer'} for q in old[n]};assert all(a[q['connection_id']]=={k:v for k,v in q.items() if k!='answer'} for q in qs);ns=support(qs);delta=Counter({u:-1 for u in oldsets[n]-ns});delta.update({u:1 for u in ns-oldsets[n]})
   if pressure(delta)>0:pool[n]=qs;newsets[n]=ns
  assert len(pool)==next(q for q in prior['rows'] if q['case']==case)['rebased_positive_proposals'];adj={n:set() for n in pool};blocked=defaultdict(set)
  for n in pool:
   for u in (newsets[n]-oldsets[n])&spans.keys():
    for owner in owners[u]-{n}:
     if owner in pool and u not in newsets[owner]:adj[n].add(owner)
     else:blocked[n].add(owner)
  comps,assignment,reverse=scc(adj);groups={}
  for comp in comps:
   if len(comp)>1:groups.setdefault(tuple(comp),set()).add('SCC')
   closure=set(comp);todo=list(comp)
   while todo:
    for dep in adj[todo.pop()]:
     if dep not in closure:closure.add(dep);todo.append(dep)
   groups.setdefault(tuple(sorted(closure)),set()).add('dependency_closure')
  groups.setdefault(tuple(sorted(pool)),set()).add('full_pool');crit={q['connection_id']:Fraction(q['criticality_numerator'],q['criticality_denominator']) for q in read(folder/'timing_round1.json')['criticalities']};basefile=Path(c['node_base_proof']).parent/'node_base.u64';base=array('Q');base.frombytes(basefile.read_bytes());history={int(u):v-spans.get(int(u),0) for u,v in state['prices'].items()};assert all(v>=0 for v in history.values());weight=10**18//(20*10**9)
  def features(qs):
   raw=sum((crit[q['connection_id']]*q['answer']['delay'] for q in qs),Fraction(0));users={}
   for q in qs:
    for eid in q['answer']['physical_edge_ids']:
     u=g['vs'][eid];users[u]=max(users.get(u,Fraction(0)),crit[q['connection_id']])
   return raw,{u:1-v for u,v in users.items()}
  f_old={n:features(old[n]) for n in pool};f_new={n:features(pool[n]) for n in pool};evaluations=[]
  for members,kinds in sorted(groups.items()):
   oldcount=Counter(u for n in members for u in oldsets[n]);newcount=Counter(u for n in members for u in newsets[n]);change=Counter(newcount);change.subtract(oldcount);pd=pressure(change);oldcoef=Counter();newcoef=Counter();oldraw=Fraction(0);newraw=Fraction(0)
   for n in members:
    oldraw+=f_old[n][0];newraw+=f_new[n][0];oldcoef.update(f_old[n][1]);newcoef.update(f_new[n][1])
   def price(u):
    outside=ledger.get(u,0)-oldcount[u];assert outside>=0;return base[u]*(1+history.get(u,0))*(1+max(0,outside-g['caps'][u]+1))+weight*spans.get(u,0)
   oldscore=oldraw+sum((v*price(u) for u,v in oldcoef.items()),Fraction(0));newscore=newraw+sum((v*price(u) for u,v in newcoef.items()),Fraction(0));external=set().union(*(blocked[n] for n in members));evaluations.append(dict(members=list(members),kinds=sorted(kinds),NETs=len(members),external_channel_blocking_owners=len(external),prospective_overflow_delta=pd,old_score=str(oldscore),candidate_score=str(newscore),objective_delta=str(newscore-oldscore),batch_criterion_pass=pd<=0 and newscore<=oldscore))
  out=D/case;out.mkdir(parents=True);payload=out/'groups.json';payload.write_text(json.dumps(evaluations)+'\n');dep=out/'dependencies.json';dep.write_text(json.dumps(dict(adjacency={str(n):sorted(vs) for n,vs in adj.items()},external_blockers={str(n):sorted(vs) for n,vs in blocked.items()},components=comps,pool_NETs=sorted(pool)))+'\n');passing=[q for q in evaluations if q['batch_criterion_pass']];row=dict(case=case,proposals=len(pool),dependency_arcs=sum(map(len,adj.values())),NETs_with_external_blocker=len(blocked),nontrivial_SCC_sizes=sorted([len(q) for q in comps if len(q)>1],reverse=True),distinct_groups_evaluated=len(evaluations),overflow_nonincreasing_groups=sum(q['prospective_overflow_delta']<=0 for q in evaluations),batch_criterion_pass_groups=len(passing),passing_group_NETs=[q['members'] for q in passing],full_pool_overflow_delta=next(q['prospective_overflow_delta'] for q in evaluations if 'full_pool' in q['kinds']));rows.append(row);print(json.dumps(row),flush=True)
  for p in [payload,dep,folder/'round1.json',folder/'receipt.json',folder/'timing_round1.json',basefile]:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_TARGET_FREE_REJECTED_GROUPS_REBASED_OVERFLOW_AND_COMMON_OBJECTIVE_EVALUATED',rows=rows,bindings=bindings,scope='Existing finite candidate pool and explicit grouping only; no completeness beyond listed groups. Dependency graph for cap1 channels, fullgraph counts for evaluation. Batch objective release rule proposed, not an original singleNET acceptance result or production forecast.'),indent=2)+'\n')
if __name__=='__main__':main()
