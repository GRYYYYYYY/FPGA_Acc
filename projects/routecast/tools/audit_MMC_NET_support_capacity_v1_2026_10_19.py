"""Capacity lower bounds from mandatory channels in the supplied NET DAGs."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from collections import defaultdict
from NET_predecessor_mandatory_channels_v1 import mandatory
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,separators=(',',':'));f.write('\n')
def main():
 M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';ap=M/'independent_prediction_verification_v1.json';a=json.loads(ap.read_text());assert a['status']=='ALL3_COMPLETE_NET_ENSEMBLE_IDENTITY_XML_DAG_EXPECTATION_AND_LEDGER_AUDIT_PASS';spec=json.loads((M/'protocol.json').read_text());graph=next(pathlib.Path(p) for p in spec['bindings'] if p.endswith('rr_graph.xml'));assert sha(graph)==spec['bindings'][str(graph)];journal=M/'NET_contributions.jsonl';assert a['bindings'][str(journal)]==sha(journal);core=R/'experiments/NET_predecessor_mandatory_core_v1_2026-10-19/verification.json';assert json.loads(core.read_text())['status']=='NET_UNION_DOMINATORS_EQUAL_EXHAUSTIVE_ALL_TREE_INTERSECTION';O=R/'experiments/mmc_NET_support_capacity_v1_2026-10-19';O.mkdir();bindings={str(p):sha(p) for p in [ap,M/'protocol.json',graph,journal,core,pathlib.Path(__file__).resolve(),R/'tools/NET_predecessor_mandatory_channels_v1.py']};write(O/'protocol.json',dict(bindings=bindings,scope='Input-only capacity necessity within exact supplied predecessor supports. Union of per-sink dominators is mandatory for every joint local-parent tree. No global shortest-support completeness, unrestricted native routability or timing claim. No new native jobs.'))
 capacities={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:capacities[int(e.get('id'))]=int(e.get('capacity'))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(capacities)==258720;consumers=defaultdict(list);owners={case:defaultdict(list) for case in spec['cases']};coverage=defaultdict(int);netids={};sinkwitness={};count=0
 for case in spec['cases']:
  ip=M/case/'NET_contribution_indices.json';assert a['bindings'][str(ip)]==sha(ip);idx=json.loads(ip.read_text());assert len(idx)==len(set(idx))==55300
  for i in idx:consumers[i].append(case)
  bindings[str(ip)]=sha(ip)
 with journal.open() as source,(O/'mandatory_contributions.jsonl').open('x') as output:
  for line in source:
   row=json.loads(line);assert row['index']==count;prepared=dict(source=row['source'],sinks=row['sinks'],choices={int(n):tuple(map(tuple,x)) for n,x in row['support_choices'].items()},distance={int(n):tuple(x) for n,x in row['support_distance'].items()});witnesses={n:s for n,s in mandatory(prepared).items() if n in capacities};netids[count]=row['net_id'];sinkwitness[count]=witnesses
   output.write(json.dumps(dict(index=count,net_id=row['net_id'],mandatory_channel_sink_witness=witnesses),separators=(',',':'))+'\n')
   for case in consumers[count]:
    coverage[case]+=1
    for n in witnesses:owners[case][n].append(count)
   count+=1
   if count%10000==0:print('CAPACITY SUPPORTS',count,flush=True)
 rows=[];selected_indices=set()
 for case in spec['cases']:
  assert coverage[case]==55300;overloaded={n:idx for n,idx in owners[case].items() if len(idx)>capacities[n]};units=sum(len(idx)-capacities[n] for n,idx in overloaded.items());certificate=None
  if overloaded:
   n=min(overloaded);idx=sorted(overloaded[n],key=lambda i:(netids[i],i))[:capacities[n]+1];assert len({netids[i] for i in idx})==len(idx);certificate=dict(node=n,capacity=capacities[n],owners=[dict(contribution_index=i,net_id=netids[i],dominated_sink=sinkwitness[i][n]) for i in idx]);selected_indices.update(idx)
  rows.append(dict(case=case,NETs=55300,mandatory_overloaded_channels=len(overloaded),unavoidable_channel_overflow_lower_bound=units,restricted_support_capacity_infeasible=bool(overloaded),certificate=certificate));print('CAPACITY RESULT',case,len(overloaded),units,flush=True)
 selected={}
 with journal.open() as f:
  for line in f:
   row=json.loads(line)
   if row['index'] in selected_indices:selected[row['index']]=row
 for row in rows:
  if row['certificate']:
   for owner in row['certificate']['owners']:
    data=selected[owner['contribution_index']];owner.update(source=data['source'],sinks=data['sinks'],support_choices=data['support_choices'],support_distance=data['support_distance'])
 bindings[str(O/'mandatory_contributions.jsonl')]=sha(O/'mandatory_contributions.jsonl');write(O/'results.json',dict(status='ALL3_SUPPLIED_NET_SUPPORT_MANDATORY_CAPACITY_BOUNDS_COMPUTED',bindings=bindings,cases=rows,unique_NET_endpoint_sets=count,independent_selected_certificates_pending=True,new_native_jobs=0,scope='Bounds within supplied acyclic parent supports only. Positive mandatory overload proves no capacity-legal joint choice from these supports, regardless parent-choice coupling or sample count. Does NOT prove unconstrained native infeasibility or infeasibility of all full-graph RC minima. No-overload means UNKNOWN, not feasible.'))
if __name__=='__main__':main()
