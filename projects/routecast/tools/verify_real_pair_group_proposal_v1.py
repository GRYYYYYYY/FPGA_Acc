"""Independent XML pair paths, shared-cost admission and scratch capacity replay."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from array import array
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_real_pair_group_proposal_v1_2026-10-20';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 v=read(D/'verification.json');assert all(sha(p)==h for p,h in v['bindings'].items());cases=read(A/'protocol.json')['cases'];needed=set();data={}
 for c in cases:
  case=c['case'];out=A/case/'native_retained/warm_timing_round_updated';frame=read(out/'round1.json');payload=read(D/case/'proposal.json');members=payload['members'];old=defaultdict(list)
  for q in frame['records']:
   if q['net_id'] in members:old[q['net_id']].append(q)
  for groups in [old,payload['archived_candidate'],payload['fresh_candidate']]:
   for recs in groups.values():
    for q in recs:needed.update(q['answer']['physical_edge_ids'])
  data[case]=c,out,frame,payload,old
 graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);edges={};caps={};spans={};weights={};eid=0;stack=[]
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
   if eid in needed:edges[eid]=int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))
   eid+=1
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 def validate(recs):
  ns=set();parents={}
  for q in recs:
   u=q['source'];seen={u};value=Fraction(0);ns.add(u)
   for eid in q['answer']['physical_edge_ids']:
    a,b,s=edges[eid];assert a==u and b not in seen;assert b not in parents or parents[b]==(a,eid);parents[b]=a,eid;seen.add(b);ns.add(b);value+=weights[s];u=b
   assert u==q['sink'] and value==q['answer']['delay']<=q['budget_integer']
  return ns
 rows=[]
 for case,(c,out,frame,payload,old) in data.items():
  ledger=Counter({int(n):v for n,v in frame['ledger'].items()});oldsets={n:validate(recs) for n,recs in old.items()};oldcount=Counter(u for ns in oldsets.values() for u in ns);outside=Counter(ledger);outside.subtract(oldcount);assert min(outside.values())>=0;crit={q['connection_id']:Fraction(q['criticality_numerator'],q['criticality_denominator']) for q in read(out/'timing_round1.json')['criticalities']};base=array('Q');base.frombytes((Path(c['node_base_proof']).parent/'node_base.u64').read_bytes());hist={int(n):v-spans.get(int(n),0) for n,v in frame['prices'].items()}
  def score(recs):
   raw=sum((crit[q['connection_id']]*q['answer']['delay'] for q in recs),Fraction(0));users=defaultdict(list)
   for q in recs:
    for eid in q['answer']['physical_edge_ids']:users[edges[eid][1]].append(crit[q['connection_id']])
   return raw+sum(((1-max(cs))*(base[u]*(1+hist.get(u,0))*(1+max(0,outside[u]-caps[u]+1))+(10**18//20000000000)*spans.get(u,0)) for u,cs in users.items()),Fraction(0))
  oldscore=sum((score(recs) for recs in old.values()),Fraction(0));states=[]
  for name,groups,plan in [('archived',payload['archived_candidate'],payload['archived_plan']),('fresh',payload['fresh_candidate'],payload['fresh_metadata']['plan'])]:
   groups={int(n):recs for n,recs in groups.items()};assert set(groups)==set(old);newsets={n:validate(recs) for n,recs in groups.items()}
   for n,recs in groups.items():
    meta={q['connection_id']:{k:v for k,v in q.items() if k!='answer'} for q in old[n]};assert len(recs)==len(meta);assert all(meta[q['connection_id']]=={k:v for k,v in q.items() if k!='answer'} for q in recs)
   newcount=Counter(u for ns in newsets.values() for u in ns);after=Counter(outside);after.update(newcount);delta=sum(max(0,v-caps[u]) for u,v in after.items())-sum(max(0,v-caps[u]) for u,v in ledger.items());newscore=sum((score(recs) for recs in groups.values()),Fraction(0));updates={str(u):after[u] for u in ledger.keys()|after.keys() if after[u]!=ledger[u]};assert plan['updates']==updates;assert {int(u):v for u,v in plan['old_owner_counts'].items()}==dict(oldcount) and {int(u):v for u,v in plan['new_owner_counts'].items()}==dict(newcount);assert Fraction(plan['old_score'])==oldscore and Fraction(plan['candidate_score'])==newscore and Fraction(plan['objective_delta'])==newscore-oldscore;assert delta==plan['prospective_overflow_delta'] and plan['accepted']==(delta<=0 and newscore<=oldscore);assert plan['accepted'];states.append((name,groups,newsets))
  scratch=Counter(outside)
  for n in sorted(old):
   recs=states[1][1][n];source=recs[0]['source'];scratch[source]+=1;ns=states[1][2][n];assert all(scratch[u]<caps[u] for u in ns-{source});scratch.update(ns-{source})
  fresh_events=payload['fresh_metadata']['events'];assert [x['net_id'] for x in fresh_events]==sorted(old);assert all(x['search_events'][0]['initial_arrivals']==[[old[x['net_id']][0]['source'],0]] for x in fresh_events);row=dict(case=case,archived_and_fresh_original_XML_budgets_and_batch_scores_exact=True,fresh_group_vacancy_mask_and_unseeded_start_pass=True,objective_delta=str(states and Fraction(payload['fresh_metadata']['plan']['objective_delta'])));rows.append(row);print(row,flush=True)
 (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL3_REAL_PAIR_GROUP_XML_BUDGET_COMMON_SCORE_AND_SCRATCH_MASK_PASS',rows=rows,bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Pure proposal verification, not runtime commit, native acceptance or independent weighted optimality certificate for real graph searches.'),indent=2)+'\n')
if __name__=='__main__':main()
