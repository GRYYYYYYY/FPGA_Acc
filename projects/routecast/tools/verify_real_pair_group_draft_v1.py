"""Independent complete-frame XML raw-delay/parent/owner ledger and epoch audit."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from array import array
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_real_pair_group_draft_v1_2026-10-20';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 proof=read(D/'verification.json');assert all(sha(p)==h for p,h in proof['bindings'].items());cases=read(A/'protocol.json')['cases'];needed=set();data={}
 for c in cases:
  case=c['case'];out=A/case/'native_retained/warm_timing_round_updated';old=read(out/'round1.json');new=read(D/case/'draft_round.json');payload=read(D/case/'proposal.json');data[case]=c,out,old,new,payload
  for q in old['records']+new['records']:needed.update(q['answer']['physical_edge_ids'])
 graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);caps={};spans={};edges={};weights={};index=0;stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   n=int(e.get('id'));caps[n]=int(e.get('capacity'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
   if e.get('type') in ('CHANX','CHANY'):
    loc=e.find('loc');spans[n]=1+max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert Fraction(t.get('R','0'))==0;value=Fraction(t.get('Tdel','0'))*10**18;assert value.denominator==1;weights[int(e.get('id'))]=value.numerator
  elif e.tag=='edge' and parent=='rr_edges':
   if index in needed:edges[index]=int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))
   index+=1
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert set(edges)==needed;rows=[]
 for case,(c,out,old,new,payload) in data.items():
  assert set(old)==set(new)=={'records','ledger','epochs','prices'};members=set(payload['members']);supports=[];recordmaps=[]
  for frame in [old,new]:
   byid={};owners=defaultdict(set);parents=defaultdict(dict)
   for q in frame['records']:
    cid=q['connection_id'];net=q['net_id'];assert cid not in byid;byid[cid]=q;u=q['source'];seen={u};owners[net].add(u);delay=0
    for eid in q['answer']['physical_edge_ids']:
     a,b,s=edges[eid];assert a==u and b not in seen and caps[b]>0;assert b not in parents[net] or parents[net][b]==(a,eid);parents[net][b]=a,eid;owners[net].add(b);seen.add(b);delay+=weights[s];u=b
    assert u==q['sink'] and delay==q['answer']['delay']<=q['budget_integer']
   assert len(byid)==15616;ledger=Counter(n for owned in owners.values() for n in owned);assert dict(ledger)=={int(n):v for n,v in frame['ledger'].items()};assert set(owners)=={int(n) for n in frame['epochs']};supports.append(owners);recordmaps.append(byid)
  assert recordmaps[0].keys()==recordmaps[1].keys();outside=0;changed=0
  for cid,q in recordmaps[0].items():
   other=recordmaps[1][cid];assert {k:v for k,v in q.items() if k!='answer'}=={k:v for k,v in other.items() if k!='answer'}
   if q['net_id'] not in members:assert q==other;outside+=1
   changed+=q['answer']['physical_edge_ids']!=other['answer']['physical_edge_ids']
  assert old['prices']==new['prices'];assert old['epochs'].keys()==new['epochs'].keys();assert all(new['epochs'][n]==v+int(int(n) in members) for n,v in old['epochs'].items());oldcount=Counter(u for n in members for u in supports[0][n]);newcount=Counter(u for n in members for u in supports[1][n]);ledger=Counter({int(n):v for n,v in old['ledger'].items()});outsideledger=Counter(ledger);outsideledger.subtract(oldcount);assert min(outsideledger.values())>=0;rebuilt=Counter(outsideledger);rebuilt.update(newcount);assert dict(+rebuilt)=={int(n):v for n,v in new['ledger'].items()};delta=sum(max(0,v-caps[u]) for u,v in rebuilt.items())-sum(max(0,v-caps[u]) for u,v in ledger.items());crit={q['connection_id']:Fraction(q['criticality_numerator'],q['criticality_denominator']) for q in read(out/'timing_round1.json')['criticalities']};base=array('Q');base.frombytes((Path(c['node_base_proof']).parent/'node_base.u64').read_bytes());history={int(n):v-spans.get(int(n),0) for n,v in old['prices'].items()}
  def score(mapping):
   value=Fraction(0)
   for n in members:
    users=defaultdict(list)
    for q in mapping.values():
     if q['net_id']!=n:continue
     value+=crit[q['connection_id']]*q['answer']['delay']
     for eid in q['answer']['physical_edge_ids']:users[edges[eid][1]].append(crit[q['connection_id']])
    for u,cs in users.items():value+=(1-max(cs))*(base[u]*(1+history.get(u,0))*(1+max(0,outsideledger[u]-caps[u]+1))+(10**18//20000000000)*spans.get(u,0))
   return value
  before=score(recordmaps[0]);after=score(recordmaps[1]);plan=payload['draft_metadata']['plan'];assert delta==plan['prospective_overflow_delta']<=0 and before==Fraction(plan['old_score']) and after==Fraction(plan['candidate_score']) and after-before==Fraction(plan['objective_delta'])<=0;assert plan['accepted'];rows.append(dict(case=case,connections_per_frame=15616,outside_group_connections_preserved=outside,changed_paths=changed,member_epochs_advanced_once=True,complete_source_and_draft_XML_raw_budgets_singleparent_and_uniqueNET_ledgers_pass=True,group_pressure_delta=delta,group_objective_delta=str(after-before)));print(rows[-1],flush=True)
 (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL3_COMPLETE_SOURCE_AND_DRAFT_XML_FRAMES_BUDGET_LEDGER_EPOCH_AND_GROUP_SCORE_PASS',rows=rows,bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Complete six-frame read-only audit. Draft objects/files only, no external concurrent commit, latest STA, legal-route or forecast-utility claim.'),indent=2)+'\n')
if __name__=='__main__':main()
