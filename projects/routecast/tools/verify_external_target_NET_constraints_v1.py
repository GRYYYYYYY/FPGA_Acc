"""Alternate XML sparse edges, full ownership and independent rational scoring."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
from array import array
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_target_NET_constraints_v1_2026-10-20';A=E/'prospective_external_family_capacity_retry_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 v=read(D/'verification.json');assert all(sha(p)==h for p,h in v['bindings'].items());cases=read(A/'protocol.json')['cases'];needed=set();frames={}
 for c in cases:
  case=c['case'];frames[case]=read(Path(c['warm'])/'native_retained/initial.json'),read(D/case/'target_records.json')
  for q in frames[case][0]['records']+frames[case][1]:needed.update(q['answer']['physical_edge_ids'])
 graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);caps={};spans={};weights={};edges={};eid=0;stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert Fraction(t.get('R','0'))==0;weights[int(e.get('id'))]=Fraction(t.get('Tdel','0'))
  elif e.tag=='node' and parent=='rr_nodes':
   n=int(e.get('id'));caps[n]=int(e.get('capacity'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
   if e.get('type') in ('CHANX','CHANY'):
    loc=e.find('loc');spans[n]=1+max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))
  elif e.tag=='edge' and parent=='rr_edges':
   if eid in needed:edges[eid]=int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))
   eid+=1
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert set(edges)==needed;results=[]
 for c in cases:
  case=c['case'];warm,target=frames[case];scale=warm['scale'];ledger={int(n):v for n,v in warm['ledger'].items()};groups=[defaultdict(list),defaultdict(list)];supports=[{},{}];base=array('Q');base.frombytes((Path(c['node_base_proof']).parent/'node_base.u64').read_bytes());crit={q['connection_id']:Fraction(q['criticality_numerator'],q['criticality_denominator']) for q in read(A/case/'off/timing_round0.json')['criticalities']};details={q['net_id']:q for q in read(D/case/'NET_constraints.json')}
  for i,records in enumerate([warm['records'],target]):
   for q in records:groups[i][q['net_id']].append(q)
   for n,recs in groups[i].items():
    support=set();parents={}
    for q in recs:
     u=q['source'];seen={u};support.add(u);delay=Fraction(0)
     for eid in q['answer']['physical_edge_ids']:
      a,b,s=edges[eid];assert a==u and b not in seen and caps[b]>0;assert b not in parents or parents[b]==(a,eid);parents[b]=a,eid;seen.add(b);support.add(b);delay+=weights[s];u=b
     assert u==q['sink'] and delay*scale==q['answer']['delay']
    supports[i][n]=support
  assert dict(Counter(n for ns in supports[0].values() for n in ns))==ledger;summary={k:Counter() for k in ['all_NETs','target_changing_clean_NETs']}
  for n,d in details.items():
   old=groups[0][n];new=groups[1][n];oldbyid={q['connection_id']:q for q in old};assert oldbyid.keys()=={q['connection_id'] for q in new};owner=supports[0][n];replacement=supports[1][n];costs={}
   for node in owner|replacement:
    others=ledger.get(node,0)-(node in owner);costs[node]=int(base[node])*(max(others-caps[node]+1,0)+1)+(scale//20000000000)*spans.get(node,0)
   def independent_score(records):
    delay_score=sum((crit[q['connection_id']]*q['answer']['delay'] for q in records),Fraction(0));users=defaultdict(list)
    for q in records:
     for eid in q['answer']['physical_edge_ids']:users[edges[eid][1]].append(crit[q['connection_id']])
    return delay_score+sum(((1-max(cs))*costs[node] for node,cs in users.items()),Fraction(0))
   oldscore=independent_score(old);newscore=independent_score(new);assert oldscore==Fraction(d['old_score']) and newscore==Fraction(d['target_score']) and newscore-oldscore==Fraction(d['objective_delta']);changes=Counter({u:-1 for u in owner-replacement});changes.update({u:1 for u in replacement-owner});pressure=sum(max(0,ledger.get(u,0)+v-caps[u])-max(0,ledger.get(u,0)-caps[u]) for u,v in changes.items());assert pressure==d['pressure_delta'];bad=[q['connection_id'] for q in new if q['answer']['delay']>oldbyid[q['connection_id']]['budget_integer']];assert bad==d['budget_violating_CIDs'];category='budget' if bad else 'pressure' if pressure>0 else 'objective' if newscore>oldscore else 'admissible';assert category==d['hierarchical_exclusion'];clean=d['endpoint_category']=='endpoint_unchanged' and (owner&spans.keys())!=(replacement&spans.keys());assert clean==d['target_changing_clean']
   for cohort in (['all_NETs','target_changing_clean_NETs'] if clean else ['all_NETs']):
    s=summary[cohort];s['NETs']+=1;s['budget_fail']+=bool(bad);s['pressure_fail']+=pressure>0;s['objective_fail']+=newscore>oldscore;s['hierarchical_'+category]+=1
  expected=next(row for row in v['rows'] if row['case']==case)['summary'];assert {k:dict(x) for k,x in summary.items()}==expected;results.append(dict(case=case,NETs=len(details),all_original_XML_raw_delays_ownership_pressure_and_rational_scores_exact=True));print(results[-1],flush=True)
 (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL17757_NET_CONSTRAINT_CLASSIFICATIONS_INDEPENDENT_XML_AND_RATIONAL_SCORE_PASS',rows=results,bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Fixed warm snapshot only; no causal sequence or aggregate feasibility inference.'),indent=2)+'\n')
if __name__=='__main__':main()
