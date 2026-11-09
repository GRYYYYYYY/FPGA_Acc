"""Independent XML/Fraction physical audit and full-state sequential pair replay."""
import json,sys,hashlib
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from independent_fraction_arc_context_v2 import load_context,arc_delay
from audit_structural_node_base_v1 import audit as audit_base
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path(sys.argv[1]).resolve();receipt=read(out/'receipt.json');assert all(sha(p)==h for p,h in receipt['bindings'].items());case=receipt['input_case'];ep=read(case['endpoint']);graph=Path(ep['inputs']['graph']['path']);xml,classes_id,classes,switches,digest=load_context(graph,ep['graph_sha256']);warm=read(out/'initial.json');assert warm==read(Path(case['model_output'])/'initial.json');scale=warm['scale'];assert all(a==b==0 for a,b in classes);queries={q['connection_id']:q for q in ep['connections']};prior={q['connection_id']:q for q in warm['records']};records=defaultdict(list)
 for q in warm['records']:records[q['net_id']].append(q)
 groups=defaultdict(set)
 for cid,q in queries.items():groups[q['net_id']].add(cid)
 cr={q['connection_id']:F(q['criticality_numerator'],q['criticality_denominator']) for q in read(Path(case['model_output'])/'timing_round0.json')['criticalities']};base=audit_base(graph,case['base_proof'],scale);caps=[xml.graph.nodes[n].capacity for n in range(len(xml.graph.nodes))];span={}
 import xml.etree.ElementTree as ET
 for _,n in ET.iterparse(graph):
  if n.tag=='node' and n.get('type') in ['CHANX','CHANY']:
   loc=n.find('loc');span[int(n.get('id'))]=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1
 def physical(net,rs):
  assert len(rs)==len(groups[net]) and {q['connection_id'] for q in rs}==groups[net];owned=set();users={};raw=F(0);parents={}
  for q in rs:
   cid=q['connection_id'];assert all(q[k]==v for k,v in queries[cid].items());assert {k:v for k,v in q.items() if k!='answer'}=={k:v for k,v in prior[cid].items() if k!='answer'};u=q['source'];seen={u};owned.add(u);delay=F(0)
   for eid in q['answer']['physical_edge_ids']:
    e=xml.graph.edges[eid];assert e.source==u and e.sink not in seen and caps[e.sink]>0;assert e.sink not in parents or parents[e.sink]==(u,eid);parents[e.sink]=(u,eid);delay+=arc_delay(classes,switches,classes_id[e.sink],e.switch_id);u=e.sink;seen.add(u);owned.add(u);users[u]=max(users.get(u,F(0)),cr[cid])
   integer=delay*scale;assert u==q['sink'] and integer.denominator==1 and integer.numerator==q['answer']['delay']<=q['budget_integer'];raw+=cr[cid]*integer
  return owned,users,raw
 descriptors={n:physical(n,rs) for n,rs in records.items()};ledger=Counter(n for owned,users,raw in descriptors.values() for n in owned);assert dict(ledger)=={int(n):x for n,x in warm['ledger'].items()};bank=read(case['bank']);bdesc={b['id']:physical(b['net_id'],b['records']) for b in bank};pairs=[json.loads(l) for l in Path(case['pairs']).read_text().splitlines()];pairs.sort(key=lambda p:(F(p['objective_delta']),p['overflow_delta'],tuple(sorted(p['NETs'])),tuple(p['candidate_ids'])));events=read(out/'events.json');assert len(events)==len(pairs)==receipt['fixed_order_count'];used=set();epochs={int(n):x for n,x in warm['epochs'].items()};commits=0
 for rank,(p,e) in enumerate(zip(pairs,events)):
  assert e['rank']==rank and e['candidate_ids']==p['candidate_ids'] and e['NETs']==p['NETs'];ns=p['NETs'];ids=p['candidate_ids']
  if used&set(ns):assert e['status']=='SKIP_NET_ALREADY_USED' and set(e)=={'rank','candidate_ids','NETs','status'};continue
  selected={bank[i]['net_id']:i for i in ids};released=Counter(node for n in ns for node in descriptors[n][0]);newdescs=dict(descriptors)
  for n,i in selected.items():newdescs[n]=bdesc[i]
  future=Counter(node for owned,users,raw in newdescs.values() for node in owned);pressure=sum(max(0,future[node]-caps[node])-max(0,ledger[node]-caps[node]) for node in set(future)|set(ledger))
  def score(descs):
   total=F(0)
   for n in ns:
    owned,users,raw=descs[n];total+=raw
    for node,c in users.items():
     other=ledger[node]-released[node];assert other>=0;cost=base[node]*(1+max(0,other-caps[node]+1))+(scale//20000000000)*span.get(node,0);total+=(1-c)*cost
   return total
  before,after=score(descriptors),score(newdescs);delta=after-before;accept=pressure<=0 and delta<=0 and (pressure<0 or delta<0);status='COMMITTED' if accept else 'RETAIN_OBJECTIVE_INCREASE' if delta>0 else 'RETAIN_OVERFLOW_INCREASE' if pressure>0 else 'RETAIN_NO_STRICT_PROGRESS';assert e['status']==status and e['overflow_delta']==pressure and F(e['old_score'])==before and F(e['candidate_score'])==after and F(e['objective_delta'])==delta
  if accept:
   descriptors=newdescs;ledger=future
   for n,i in selected.items():records[n]=bank[i]['records'];epochs[n]+=1
   used.update(ns);commits+=1
 final=read(out/'sketch.json');assert final['records']==sorted([q for rs in records.values() for q in rs],key=lambda q:q['connection_id']);assert {int(n):x for n,x in final['ledger'].items()}==dict(ledger) and {int(n):x for n,x in final['epochs'].items()}==epochs;assert sorted(used)==receipt['used_NETs'] and commits==receipt['committed_groups'];assert final['graph_sha256']==digest and final['completed_connections']==final['required_connections']==len(queries)==2493 and not final['eligible_for_legal_route_commit'];assert final['overflow_units']==sum(max(0,x-caps[n]) for n,x in ledger.items()) and final['overflow_nodes']==sum(x>caps[n] for n,x in ledger.items());independent=Counter(node for q in final['records'] for node in ({q['source']}|{xml.graph.edges[e].sink for e in q['answer']['physical_edge_ids']}));assert dict(independent)=={int(n):x for n,x in final['independent_connection_ledger'].items()};assert final['history']==warm['history']=={}
 bindings={**receipt['bindings'],str(out/'receipt.json'):sha(out/'receipt.json'),str(Path(__file__)):sha(__file__)};(out/'verification.json').write_text(json.dumps({'status':'COMPLETE_PAIR_APPLICATION_XML_FRACTION_AND_ATOMIC_REPLAY_PASS','case':receipt['case'],'events':len(events),'committed_groups':commits,'all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass':True,'fixed_order_current_ledger_common_objective_strict_progress_and_disjoint_NETs_pass':True,'bindings':bindings,'scope':'Isolated sketch state, complete candidate/initial/final physical and per-event group trajectory checked; no runtime intermediate-memory atomicity, exact native routing, quality or full paid benefit claim.'},indent=2)+'\n');print('PAIR_APPLICATION_PASS',receipt['case'],commits)
if __name__=='__main__':main()
