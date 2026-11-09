"""Independent bit-intersections and exact mandatory-NET capacity certificates."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_recorded_pool_capacity_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=D/'verification.json';v=read(source);assert all(sha(p)==h for p,h in v['bindings'].items());graphs={};rows=[]
 for row in v['rows']:
  ep=read(row['endpoint']);graph=ep['inputs']['graph']['path']
  if graph not in graphs:
   root=ET.parse(graph).getroot();nodes=list(root.find('rr_nodes'));graphs[graph]=([int(e.get('sink_node')) for e in root.find('rr_edges')],{int(n.get('id')):(int(n.get('capacity')),n.get('type')) for n in nodes})
  dest,nodes=graphs[graph];out=Path(row['output']);initial=defaultdict(list);pool=defaultdict(set);observations=Counter()
  def add(net,records):
   mask=0
   for q in records:
    mask|=1<<q['source']
    for e in q['answer']['physical_edge_ids']:mask|=1<<dest[e]
   pool[net].add(mask);observations[net]+=1
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for n,records in initial.items():add(n,records)
  for rnd in read(out/'receipt.json')['rounds']:
   for e in rnd['events']:
    for key in ['records','rejected_records']:
     if key in e:add(e['net_id'],e[key])
  forced=defaultdict(list);possible=defaultdict(list)
  def scatter(mask,net,table):
   while mask:
    bit=mask&-mask;table[bit.bit_length()-1].append(net);mask-=bit
  for net,choices in pool.items():
   common=-1;union=0
   for mask in choices:common&=mask;union|=mask
   scatter(common,net,forced);scatter(union,net,possible)
  conflicts=[{'node':n,'type':nodes[n][1],'capacity':nodes[n][0],'mandatory_NETs':sorted(nets)} for n,nets in sorted(forced.items()) if len(nets)>nodes[n][0]];payload=read(row['payload']);assert conflicts==payload['conflicts'];assert {str(n):len(c) for n,c in pool.items()}==payload['pool_ownership_pattern_counts'];assert {str(n):c for n,c in observations.items()}==payload['candidate_observations'];assert len(conflicts)==row['mandatory_overcapacity_nodes'];assert sum(len(c['mandatory_NETs'])-c['capacity'] for c in conflicts)==row['mandatory_overflow_unit_lower_bound'];assert sum(len(nets)>nodes[n][0] for n,nets in possible.items())==row['possible_contention_nodes'];rows.append({key:row[key] for key in ['case','initializer','timing_policy','priority','mandatory_overcapacity_nodes','mandatory_overcapacity_CHANNELs','mandatory_overflow_unit_lower_bound','result']});print(row['case'],row['initializer'],row['timing_policy'],row['priority'],'CAPACITY_CERT_PASS',flush=True)
 assert len(rows)==72
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL72_MANDATORY_OWNER_CAPACITY_CERTIFICATES_INDEPENDENT_BITSET_PASS','rows':rows,'bindings':{str(source):sha(source),str(Path(__file__)):sha(__file__),str(D/'protocol.json'):sha(D/'protocol.json')},'scope':'No target labels. A conflict certifies finite bank has no all-capacity-feasible point selection, not original graph UNSAT or quality-gate impossibility. Empty conflict sets do not establish feasibility; no joint solver run.'},indent=2)+'\n');print('ALL72_CAPACITY_CERTS_PASS')
if __name__=='__main__':main()
