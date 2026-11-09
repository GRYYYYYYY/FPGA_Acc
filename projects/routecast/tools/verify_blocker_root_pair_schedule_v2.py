"""Independent all-RR source ownership and complete root/blocker schedule check."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prospective_external_family_blocker_root_pair_schedule_v2_2026-10-20';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 proof=read(S/'verification.json');assert all(sha(p)==h for p,h in proof['bindings'].items());cases=read(A/'protocol.json')['cases'];needed=set();data={}
 for c in cases:
  base=A/c['case']/'native_retained/warm_timing_round_updated';state=read(base/'round1.json');events=read(base/'receipt.json')['rounds'][1]['events'];candidates={q['net_id']:q['rejected_records'] for q in events if 'rejected_records' in q and q['prospective_overflow_delta']>0};data[c['case']]=state,candidates
  for q in state['records']:needed.update(q['answer']['physical_edge_ids'])
  for recs in candidates.values():
   for q in recs:needed.update(q['answer']['physical_edge_ids'])
 graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);edges={};caps={};eid=0;stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':caps[int(e.get('id'))]=int(e.get('capacity'))
  elif e.tag=='edge' and parent=='rr_edges':
   if eid in needed:edges[eid]=int(e.get('src_node')),int(e.get('sink_node'))
   eid+=1
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 def owned(recs):
  ns=set()
  for q in recs:
   u=q['source'];ns.add(u)
   for eid in q['answer']['physical_edge_ids']:a,b=edges[eid];assert a==u;u=b;ns.add(u)
   assert u==q['sink']
  return ns
 rows=[]
 for case,(state,candidates) in data.items():
  old=defaultdict(list)
  for q in state['records']:old[q['net_id']].append(q)
  oldsets={n:owned(qs) for n,qs in old.items()};ledger=Counter(u for ns in oldsets.values() for u in ns);assert dict(ledger)=={int(n):v for n,v in state['ledger'].items()};owners=defaultdict(set)
  for n,ns in oldsets.items():
   for u in ns:owners[u].add(n)
  pairs=defaultdict(lambda:defaultdict(set));roots=set()
  for root,recs in candidates.items():
   ns=owned(recs);added=ns-oldsets[root];removed=oldsets[root]-ns;delta=sum(max(0,ledger[u]+1-caps[u])-max(0,ledger[u]-caps[u]) for u in added)+sum(max(0,ledger[u]-1-caps[u])-max(0,ledger[u]-caps[u]) for u in removed)
   if delta<=0:continue
   roots.add(root)
   for u in added:
    if ledger[u]<caps[u]:continue
    for owner in owners[u]:pairs[tuple(sorted((root,owner)))][root].add(u)
  schedule=read(S/case/'schedule.json');assert [tuple(q['members']) for q in schedule]==sorted(pairs);assert set().union(*(set(q['trigger_roots']) for q in schedule))==roots
  for q in schedule:
   expected=pairs[tuple(q['members'])];assert q['trigger_roots']==sorted(expected);assert q['pressure_reasons']==[dict(root=n,blocked_nodes=sorted(vs)) for n,vs in sorted(expected.items())];assert q['connections']==sum(len(old[n]) for n in q['members']) and q['maximum_member_fanout']==max(len(old[n]) for n in q['members'])
  row=dict(case=case,roots=len(roots),pairs=len(schedule),all_original_RR_pressure_owners_reasons_and_pair_order_exact=True);rows.append(row);print(row,flush=True)
 (S/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL3_ALL_RR_ROOT_BLOCKER_SCHEDULES_INDEPENDENT_XML_OWNER_RECONSTRUCTION_PASS',rows=rows,bindings={str(S/'verification.json'):sha(S/'verification.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Preparation only, no search or target labels.'),indent=2)+'\n')
if __name__=='__main__':main()
