"""Independent bit-vector distance enumeration and direct printed target NET sets."""
import json,re,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_candidate_coverage_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';v=read(p);assert all(sha(n)==h for n,h in v['bindings'].items());graphs={};rows=[]
 for row in v['rows']:
  ep=read(row['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(e.attrib['sink_node']) for _,e in ET.iterparse(g) if e.tag=='edge']
  dest=graphs[g];ids=[json.loads(x)['id'] for x in Path(row['resources']).read_text().splitlines()];masks={n:1<<i for i,n in enumerate(ids)};names={name:int(n) for n,name in ep['net_names'].items()};target=defaultdict(int);net=None
  for line in Path(row['target_route']).read_text().splitlines():
   m=re.match(r'Net\s+\d+\s+\((.*?)\)',line)
   if m:net=names.get(m[1]);continue
   m=re.match(r'\s*Node:\s*(\d+)',line)
   if m and net is not None:target[net]|=masks.get(int(m[1]),0)
  target={n:x for n,x in target.items() if n in {q['net_id'] for q in ep['connections']}};out=Path(row['output']);initial=defaultdict(list);final=defaultdict(list)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for q in read(out/'round15.json')['records']:final[q['net_id']].append(q)
  def bits(records):
   value=0
   for q in records:
    for eid in q['answer']['physical_edge_ids']:value|=masks.get(dest[eid],0)
   return value
  minimum={n:10**9 for n in initial};unique=defaultdict(set);observations=defaultdict(int)
  def update(n,records):
   mask=bits(records);distance=(mask^target[n]).bit_count();minimum[n]=min(minimum[n],distance);unique[n].add(mask);observations[n]+=1
  for n,rs in initial.items():update(n,rs)
  receipt=read(out/'receipt.json')
  for rnd in receipt['rounds']:
   for e in rnd['events']:
    candidates=[e[k] for k in ['records','rejected_records'] if k in e];assert len(candidates)<=1
    for records in candidates:update(e['net_id'],records)
  payload=read(row['payload']);assert len(payload)==1074
  for q in payload:
   n=q['net_id'];assert q['minimum_stored_support_error']==minimum[n] and q['unique_CHANNEL_supports']==len(unique[n]) and q['candidate_observations']==observations[n];assert q['initial_error']==(bits(initial[n])^target[n]).bit_count() and q['final16_error']==(bits(final[n])^target[n]).bit_count();bestmask=0
   for node in q['best']['CHANNEL_nodes']:bestmask|=masks[node]
   assert bestmask in unique[n] and (bestmask^target[n]).bit_count()==minimum[n] and q['selection_gap_at16']==q['final16_error']-minimum[n]
  assert sum(q['minimum_stored_support_error'] for q in payload)==row['finite_pool_min_support_error_sum'];rows.append({'case':row['case'],'initializer':row['initializer'],'timing_policy':row['timing_policy'],'NETs':1074,'all_candidate_minima_counts_and_witnesses_bit_vector_verified':True})
 assert len(rows)==36
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL38664_NET_POOL_MINIMA_AND_WITNESSES_INDEPENDENT_BIT_VECTOR_PASS','rows':rows,'NET_pools':38664,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Separate direct printed-target parser and bit-vector distance/unique-support enumeration; shares original graph edge mapping semantics. Finite pool perNET lower bounds only, not joint legal routing or resource rank optimum.'},indent=2)+'\n');print('ALL38664_NET_POOL_MINIMA_AND_WITNESSES_INDEPENDENT_BIT_VECTOR_PASS')
if __name__=='__main__':main()
