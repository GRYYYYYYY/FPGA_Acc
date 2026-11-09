"""Independent full-ledger rebuild for every reported feasible exchange."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_fixed_nominal_pair_exchange_v1_2026-10-19';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 result=read(D/'diagnosis.json');assert all(sha(p)==h for p,h in result['bindings'].items());cases=read(A/'protocol.json')['cases'];data={};needed=set()
 for c in cases:
  case=c['case'];base=A/case/'native_retained/warm_timing_round_updated';state=read(base/'round1.json');recs=defaultdict(list)
  for q in state['records']:recs[q['net_id']].append(q)
  candidates={e['net_id']:e['rejected_records'] for e in read(base/'receipt.json')['rounds'][1]['events'] if 'rejected_records' in e};pairs=read(D/case/'feasible_pairs.json');data[case]=(state,recs,candidates,pairs)
  for q in state['records']:needed.update(q['answer']['physical_edge_ids'])
  for pair in pairs:
   for net in pair['nets']:
    for q in candidates[net]:needed.update(q['answer']['physical_edge_ids'])
 graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);caps={};edges={};eid=0;stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':caps[int(e.get('id'))]=int(e.get('capacity'))
  if e.tag=='edge' and parent=='rr_edges':
   if eid in needed:edges[eid]=int(e.get('src_node')),int(e.get('sink_node'))
   eid+=1
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 def ownership(records):
  nodes=set()
  for q in records:
   u=q['source'];nodes.add(u)
   for e in q['answer']['physical_edge_ids']:a,b=edges[e];assert a==u;u=b;nodes.add(u)
   assert u==q['sink']
  return nodes
 def ledger(recs):return Counter(n for rows in recs.values() for n in ownership(rows))
 def overflow(l):return sum(max(0,v-caps[n]) for n,v in l.items())
 rows=[]
 for case,(state,recs,candidates,pairs) in data.items():
  original=ledger(recs);assert dict(original)=={int(n):v for n,v in state['ledger'].items()}
  for pair in pairs:
   combined=dict(recs);individual=[]
   for net in pair['nets']:
    one=dict(recs);one[net]=candidates[net];individual.append(overflow(ledger(one))-overflow(original));combined[net]=candidates[net]
   final=ledger(combined);delta=overflow(final)-overflow(original);changes={str(n):final[n]-original[n] for n in set(final)|set(original) if final[n]!=original[n]};assert changes==pair['changes'] and individual==pair['individual_overflow_deltas'] and all(x>0 for x in individual) and delta==pair['joint_overflow_delta']<=0
  rows.append(dict(case=case,all_reported_pairs_full_rebuild_exact=len(pairs)));print(rows[-1],flush=True)
 (D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL3_REPORTED_PAIRS_ALTERNATE_XML_FULL_LEDGER_REBUILDS_PASS',rows=rows,bindings={str(D/'diagnosis.json'):sha(D/'diagnosis.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Verifies every reported feasible pair, not the completeness of enumeration or common objective acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
