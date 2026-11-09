"""Independent deletion/reachability verification of selected capacity witnesses."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_NET_support_capacity_v1_2026-10-19';rp=O/'results.json'
 if not rp.exists():raise SystemExit('NOT_READY: supplied-support capacity results required')
 result=json.loads(rp.read_text());assert result['status']=='ALL3_SUPPLIED_NET_SUPPORT_MANDATORY_CAPACITY_BOUNDS_COMPUTED'
 for p,h in result['bindings'].items():assert sha(p)==h,p
 M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';journal=M/'NET_contributions.jsonl';required={owner['contribution_index'] for row in result['cases'] if row['certificate'] for owner in row['certificate']['owners']};original={}
 for line in journal.open():
  data=json.loads(line)
  if data['index'] in required:original[data['index']]=data
 assert set(original)==required;targets={row['certificate']['node'] for row in result['cases'] if row['certificate']};graph=next(pathlib.Path(p) for p in result['bindings'] if p.endswith('rr_graph.xml'));caps={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   n=int(e.get('id'))
   if n in targets:assert e.get('type') in ['CHANX','CHANY'];caps[n]=int(e.get('capacity'))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 rows=[];verified=0;bindings={str(p):sha(p) for p in [rp,journal,graph,pathlib.Path(__file__).resolve()]}
 for row in result['cases']:
  certificate=row['certificate']
  if not certificate:assert not row['restricted_support_capacity_infeasible'];rows.append(dict(case=row['case'],status='UNKNOWN_NO_POSITIVE_MANDATORY_NODE_CERTIFICATE'));continue
  n=certificate['node'];capacity=caps[n];assert capacity==certificate['capacity'] and capacity>0;owners=certificate['owners'];assert len(owners)==capacity+1 and len({o['net_id'] for o in owners})==len(owners);ip=M/row['case']/'NET_contribution_indices.json';indices=set(json.loads(ip.read_text()));bindings[str(ip)]=sha(ip)
  for owner in owners:
   index=owner['contribution_index'];assert index in indices;data=original[index];assert owner['net_id']==data['net_id']
   for key in ['source','sinks','support_choices','support_distance']:assert owner[key]==data[key]
   source=owner['source'];sink=owner['dominated_sink'];assert sink in owner['sinks'] and n!=source and n!=sink;parents={int(k):v for k,v in owner['support_choices'].items()};labels={int(k):tuple(v) for k,v in owner['support_distance'].items()};order=sorted(labels,key=lambda k:(labels[k][1],k));assert set(parents)==set(labels)-{source} and labels[source]==(0,0)
   reach={source};without={source}
   for node in order:
    if node==source:continue
    assert parents[node]
    for p,_ in parents[node]:assert p in labels and labels[p][1]+1==labels[node][1]
    if any(p in reach for p,_ in parents[node]):reach.add(node)
    if node!=n and any(p in without for p,_ in parents[node]):without.add(node)
   assert sink in reach and sink not in without;verified+=1
  assert row['restricted_support_capacity_infeasible'];rows.append(dict(case=row['case'],status='SUPPLIED_SUPPORT_CAPACITY_INFEASIBLE_CERTIFIED',node=n,capacity=capacity,distinct_NETs=len(owners)))
 proof=dict(status='SELECTED_SUPPLIED_SUPPORT_CAPACITY_CERTIFICATES_INDEPENDENTLY_VERIFIED',bindings=bindings,cases=rows,NET_deletion_witnesses_verified=verified,new_native_jobs=0,scope='Deleting one physical CHAN resource disconnects a required sink for more distinctNETs than capacity, within the exact supplied predecessor DAGs. Independent reachability, not dominator implementation. No assertion that supplied supports cover all global RC minima; no unrestricted native routing infeasibility or new predictor/utility claim.')
 with (O/'independent_certificate_verification_v1.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
 print(proof['status'],verified,flush=True)
if __name__=='__main__':main()
