"""Independent all-group overflow; full-ledger/shared-score checks and prior pairs."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from array import array
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_rejected_candidate_groups_v1_2026-10-20';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';P=E/'prospective_external_family_fixed_nominal_pair_exchange_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 proof=read(D/'verification.json');assert all(sha(p)==h for p,h in proof['bindings'].items());cases=read(A/'protocol.json')['cases'];data={};needed=set()
 for c in cases:
  case=c['case'];out=A/case/'native_retained/warm_timing_round_updated';state=read(out/'round1.json');old=defaultdict(list)
  for q in state['records']:old[q['net_id']].append(q)
  poolids=read(D/case/'dependencies.json')['pool_NETs'];events=read(out/'receipt.json')['rounds'][1]['events'];pool={x['net_id']:x['rejected_records'] for x in events if x['net_id'] in poolids};assert set(pool)==set(poolids);data[case]=c,out,state,old,pool
  for recs in list(old.values())+list(pool.values()):
   for q in recs:needed.update(q['answer']['physical_edge_ids'])
 graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);caps={};spans={};edges={};weights={};index=0;stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   n=int(e.get('id'));caps[n]=int(e.get('capacity'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
   if e.get('type') in ('CHANX','CHANY'):
    loc=e.find('loc');spans[n]=1+max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert Fraction(t.get('R','0'))==0;weights[int(e.get('id'))]=Fraction(t.get('Tdel','0'))*10**18
  elif e.tag=='edge' and parent=='rr_edges':
   if index in needed:edges[index]=int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))
   index+=1
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 def ownership(recs):
  ns=set();parents={}
  for q in recs:
   u=q['source'];ns.add(u);value=Fraction(0);seen={u}
   for eid in q['answer']['physical_edge_ids']:
    a,b,s=edges[eid];assert a==u and b not in seen;assert b not in parents or parents[b]==(a,eid);parents[b]=a,eid;seen.add(b);ns.add(b);value+=weights[s];u=b
   assert u==q['sink'] and value==q['answer']['delay']<=q['budget_integer']
  return ns
 results=[]
 for case,(c,out,state,old,pool) in data.items():
  os={n:ownership(recs) for n,recs in old.items()};ns={n:ownership(recs) for n,recs in pool.items()};ledger=Counter(u for support in os.values() for u in support);assert dict(ledger)=={int(n):v for n,v in state['ledger'].items()};deltas={}
  for n in pool:
   delta=Counter(ns[n]);delta.subtract(os[n]);deltas[n]=delta
  def overflow_delta(delta):return sum(max(0,ledger[u]+v-caps[u])-max(0,ledger[u]-caps[u]) for u,v in delta.items())
  def group_pressure(members):
   combined=Counter()
   for n in members:combined.update(deltas[n])
   return overflow_delta(combined)
  groups=read(D/case/'groups.json');assert all(group_pressure(g['members'])==g['prospective_overflow_delta'] for g in groups);noninc=[g for g in groups if g['prospective_overflow_delta']<=0];checks={tuple(g['members']):g for g in groups if g['prospective_overflow_delta']<=0 or 'full_pool' in g['kinds']};pairfile=P/case/'feasible_pairs.json'
  for pair in read(pairfile):checks.setdefault(tuple(pair['nets']),None)
  base=array('Q');base.frombytes((Path(c['node_base_proof']).parent/'node_base.u64').read_bytes());crit={q['connection_id']:Fraction(q['criticality_numerator'],q['criticality_denominator']) for q in read(out/'timing_round1.json')['criticalities']};history={int(n):v-spans.get(int(n),0) for n,v in state['prices'].items()};pair_checks=[]
  for members,reported in checks.items():
   outside=Counter(u for n,recs in os.items() if n not in members for u in recs);trial=dict(old)
   for n in members:trial[n]=pool[n]
   rebuilt=Counter(u for n,recs in trial.items() for u in (ns[n] if n in members else os[n]));delta=sum(max(0,v-caps[u]) for u,v in rebuilt.items())-sum(max(0,v-caps[u]) for u,v in ledger.items());assert delta==group_pressure(members)
   def score(recs):
    users=defaultdict(list);value=Fraction(0)
    for q in recs:
     coefficient=crit[q['connection_id']];value+=coefficient*q['answer']['delay']
     for eid in q['answer']['physical_edge_ids']:users[edges[eid][1]].append(coefficient)
    for u,coeffs in users.items():value+=(1-max(coeffs))*(base[u]*(1+history.get(u,0))*(1+max(0,outside[u]-caps[u]+1))+(10**18//20000000000)*spans.get(u,0))
    return value
   before=sum((score(old[n]) for n in members),Fraction(0));after=sum((score(pool[n]) for n in members),Fraction(0))
   if reported is not None:assert before==Fraction(reported['old_score']) and after==Fraction(reported['candidate_score']) and after-before==Fraction(reported['objective_delta']) and reported['batch_criterion_pass']==(delta<=0 and after<=before)
   else:pair_checks.append(dict(members=list(members),pressure_delta=delta,objective_delta=str(after-before),batch_criterion_pass=delta<=0 and after<=before))
  owners=defaultdict(set)
  for n,support in os.items():
   for u in support:owners[u].add(n)
  external=set();retaining=set()
  for n in pool:
   for u in (ns[n]-os[n])&spans.keys():
    for other in owners[u]-{n}:
     if other not in pool:external.add(n)
     elif u in ns[other]:retaining.add(n)
  row=dict(case=case,all_group_pressure_deltas_verified=len(groups),reported_nonincreasing_groups=len(noninc),full_ledger_and_common_objective_groups=len(checks),prior_pair_common_objective_checks=pair_checks,NETs_blocked_by_owners_without_any_candidate=len(external),NETs_blocked_by_candidate_owners_that_retain_resource=len(retaining));results.append(row);print(json.dumps(row),flush=True)
 (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL_GROUP_OVERFLOW_EXACT_REPRESENTATIVE_FULL_LEDGER_COMMON_OBJECTIVE_AND_PRIOR_PAIRS_VERIFIED',rows=results,bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)},scope='All listed group pressure deltas; common objective and full-ledger rebuild for full-pool, nonincreasing-pressure groups and prior feasible pairs only. Original field NETs_with_external_blocker means unresolved blocker including candidate owners that retain channel; corrected disjointness not assumed. No batch commits/forecast claim.'),indent=2)+'\n')
if __name__=='__main__':main()
