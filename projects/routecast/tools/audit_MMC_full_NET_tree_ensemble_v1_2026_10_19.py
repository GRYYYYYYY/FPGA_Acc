"""Independent full output audit; no target routing labels, no producer predict call."""
import pathlib,json,hashlib,random,itertools,math,xml.etree.ElementTree as ET
from collections import defaultdict,Counter
from fractions import Fraction
from array import array
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def audit_probabilities(record):
 source=record['source'];sinks=record['sinks'];choices={int(n):tuple(map(tuple,row)) for n,row in record['support_choices'].items()};labels={int(n):tuple(x) for n,x in record['support_distance'].items()};prob={int(n):Fraction(x) for n,x in record['probabilities'].items()};assert set(choices)==set(labels)-{source};assert labels[source]==(0,0) and prob[source]==1 and all(0<x<=1 for x in prob.values()) and set(prob)<=set(labels)
 if len(sinks)==1:
  assert record['mode']=='exact_single_sink';children=defaultdict(list)
  for v,row in choices.items():
   for u,_ in row:children[u].append((v,Fraction(1,len(row))))
  sink=sinks[0]
  # Check every DAG conservation equation rather than calling production DP.
  for n in labels:
   expected=Fraction(int(n==sink))+sum(prob.get(v,0)*weight for v,weight in children[n]);assert prob.get(n,0)==expected
 else:
  keys=sorted(choices);assignments=math.prod(len(choices[n]) for n in keys);counts=Counter()
  def visit(parents):
   nodes={source}
   for sink in sinks:
    cursor=sink;seen=set()
    while cursor!=source:
     assert cursor not in seen;seen.add(cursor);nodes.add(cursor);cursor=parents[cursor][0]
   return nodes
  if assignments<=4096:
   assert record['mode']=='exact_multi_sink_local_parents'
   for values in itertools.product(*(choices[n] for n in keys)):counts.update(visit(dict(zip(keys,values))))
   denominator=assignments
  else:
   assert record['mode']=='sampled_shared_parent_multi_sink'
   for i in range(16):
    digest=hashlib.sha256(f"19:{record['net_id']}:{i}".encode()).digest();rng=random.Random(int.from_bytes(digest,'big'));parents={n:choices[n][rng.randrange(len(choices[n]))] for n in keys};counts.update(visit(parents))
   denominator=16
  assert prob=={n:Fraction(x,denominator) for n,x in counts.items()}
 return choices,labels,prob

def main():
 O=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';rp=O/'receipt.json'
 if not rp.exists():raise SystemExit('NOT_READY: complete three-layout producer receipt required')
 receipt=json.loads(rp.read_text());assert receipt['status']=='ALL3_COMPLETE_55300_NET_ENSEMBLE_PREDICTIONS_PRODUCED'
 for p,h in receipt['bindings'].items():assert sha(p)==h,p
 pp=O/'protocol.json';spec=json.loads(pp.read_text());assert spec['exact_assignment_limit']==4096 and spec['samples']==16 and spec['seed']==19
 graph=next(pathlib.Path(p) for p in spec['bindings'] if p.endswith('rr_graph.xml'));us=array('I');vs=array('I');weights=array('Q');caps=array('I');kinds=[];switches={};stack=[]
 print('FULL AUDIT ORIGINAL XML START',flush=True)
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert Fraction(t.get('Cinternal','0'))==0 and e.get('type') in ['buffer','mux','tristate'];value=Fraction(t.get('Tdel','0'))*10**18;assert value.denominator==1 and value>=0;switches[int(e.get('id'))]=int(value)
  elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));weights.append(switches[int(e.get('switch_id'))])
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert len(caps)==904438 and len(us)==8097539;I=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19';consumers=defaultdict(list);expected={};ledgers={};modes={};bindings={str(rp):sha(rp),str(pp):sha(pp),str(graph):sha(graph),str(pathlib.Path(__file__).resolve()):sha(__file__)}
 for case in spec['cases']:
  ep=I/case/'demand/endpoints.json';meta=json.loads(ep.read_text());groups=defaultdict(list)
  for q in meta['connections']:groups[q['net_id']].append(q)
  assert len(groups)==55300 and len(meta['connections'])==115572;ip=O/case/'NET_contribution_indices.json';indices=json.loads(ip.read_text());assert len(indices)==55300
  for (net,qs),index in zip(sorted(groups.items()),indices):
   sources={q['source'] for q in qs};assert len(sources)==1;expected[case,net]=(sources.pop(),tuple(sorted({q['sink'] for q in qs})));consumers[index].append((case,net))
  ledgers[case]=Counter();modes[case]=Counter();bindings[str(ep)]=sha(ep);bindings[str(ip)]=sha(ip)
 seen_keys=set();count=0;support_edges=0;covered=Counter();journal=O/'NET_contributions.jsonl';assert receipt['bindings'][str(journal)]==sha(journal)
 with journal.open() as stream:
  for line in stream:
   row=json.loads(line);assert row['index']==count and count in consumers;key=(row['net_id'],row['source'],tuple(row['sinks']));assert key not in seen_keys;seen_keys.add(key);choices,labels,prob=audit_probabilities(row);source=row['source'];assert kinds[source]=='SOURCE' and all(kinds[s]=='SINK' for s in row['sinks'])
   for n in labels:assert 0<=n<len(caps) and caps[n]>0
   for n,parents in choices.items():
    assert parents and len(set(parents))==len(parents) and kinds[n]!='SOURCE'
    for u,e in parents:
     assert 0<=e<len(us) and us[e]==u and vs[e]==n and kinds[u]!='SINK';assert labels[n]==(labels[u][0]+weights[e],labels[u][1]+1);support_edges+=1
   for case,net in consumers[count]:
    assert net==row['net_id'] and expected[case,net]==(source,tuple(row['sinks']));ledgers[case].update(prob);modes[case][row['mode']]+=1;covered[case]+=1
   count+=1
   if count%1000==0:print('FULL AUDIT NET CONTRIBUTIONS',count,flush=True)
 assert count==receipt['unique_NET_endpoint_sets'] and set(consumers)==set(range(count));rows=[]
 for case in spec['cases']:
  assert covered[case]==55300;lp=O/case/'expected_unique_NET_occupancy.json';actual={int(n):Fraction(x) for n,x in json.loads(lp.read_text()).items()};assert actual==dict(ledgers[case]);bindings[str(lp)]=sha(lp);rows.append(dict(case=case,NETs=55300,connections=115572,modes=dict(modes[case]),exact_ledger_reconstruction_pass=True))
 bindings[str(journal)]=sha(journal)
 with (O/'independent_prediction_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_COMPLETE_NET_ENSEMBLE_IDENTITY_XML_DAG_EXPECTATION_AND_LEDGER_AUDIT_PASS',bindings=bindings,rows=rows,unique_NET_endpoint_sets=count,support_edges_checked=support_edges,global_minimum_dual_for_all_NETs_pending=True,forecast_quality_pending=True,scope='Complete NET expectation and ledger audit with original XML physical arcs/RC/terminal constraints. Single-sink DAG conservation; multi-sink exact enumeration or deterministic16sample reconstruction. Not full global shortest dual/STA, quality, heldout or net-time gain.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
