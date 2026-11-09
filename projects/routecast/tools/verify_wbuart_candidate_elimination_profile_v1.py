"""Independent bitset input scopes and factor-bucket symbolic elimination replay."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from itertools import combinations
from math import prod
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_candidate_elimination_profile_v1_2026-10-20'
def read(p):
 p=Path(p)
 if any(x in p.parts for x in ['cold','utility','specifications']) or 'label' in p.name or 'comparison' in p.name:raise ValueError('target input forbidden')
 return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=D/'verification.json';v=read(source);assert all(sha(p)==h for p,h in v['bindings'].items());graphs={};rows=[];eliminations=0
 for row in v['rows']:
  ep=read(row['endpoint']);graph=ep['inputs']['graph']['path']
  if graph not in graphs:
   root=ET.parse(graph).getroot();graphs[graph]=([int(e.get('sink_node')) for e in root.find('rr_edges')],{int(n.get('id')) for n in root.find('rr_nodes') if n.get('type') in ['CHANX','CHANY'] and int(n.get('capacity'))>0})
  dest,channels=graphs[graph];out=Path(row['output']);initial=defaultdict(list);pool=defaultdict(set)
  def add(net,rs):
   mask=0
   for q in rs:
    for edge in q['answer']['physical_edge_ids']:
     if dest[edge] in channels:mask|=1<<dest[edge]
   pool[net].add(mask)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for net,rs in initial.items():add(net,rs)
  for rnd in read(out/'receipt.json')['rounds']:
   for event in rnd['events']:
    rs=event.get('records',event.get('rejected_records'))
    if rs is not None:add(event['net_id'],rs)
  cards={n:len(c) for n,c in pool.items()};users=defaultdict(set)
  for net,choices in pool.items():
   union=0;common=-1
   for mask in choices:union|=mask;common&=mask
   mask=union&~common
   while mask:bit=mask&-mask;users[bit.bit_length()-1].add(net);mask-=bit
  scopes=defaultdict(list)
  for node in sorted(channels):scopes[tuple(sorted(users[node]))].append(node)
  p=read(row['payload']);assert cards=={int(n):d for n,d in p['cardinalities'].items()};expected=[{'NETs':list(s),'CHANNELs':ns,'states':prod(cards[n] for n in s)} for s,ns in sorted(scopes.items())];assert expected==p['resource_factor_scopes'];fixed={n for n,d in cards.items() if d==1};assert sorted(fixed)==p['fixed_NETs'];active=set(cards)-fixed;factors=[set(s)-fixed for s in scopes];max_bag=1;max_sep=1;sum_bag=0;sum_sep=0;width=0
  for step in p['steps']:
   buckets=defaultdict(set);edges=set()
   for f in factors:
    for n in f:buckets[n].update(f)
    edges.update(combinations(sorted(f),2))
   candidate_scores={};candidate_missing={}
   for n in active:
    others=buckets[n]-{n};missing=[list(e) for e in combinations(sorted(others),2) if e not in edges];candidate_scores[n]=[len(missing),cards[n]*prod(cards[x] for x in others),len(others),n];candidate_missing[n]=missing
   chosen=min(active,key=lambda n:candidate_scores[n]);others=buckets[chosen]-{chosen};assert chosen==step['NET'] and step['minfill_score']==candidate_scores[chosen] and step['neighbors']==sorted(others) and step['fill_edges']==candidate_missing[chosen];sep=prod(cards[x] for x in others);bag=sep*cards[chosen];assert step['separator_states']==sep and step['bag_states']==bag;max_bag=max(max_bag,bag);max_sep=max(max_sep,sep);sum_bag+=bag;sum_sep+=sep;width=max(width,len(others));factors=[f for f in factors if chosen not in f]+[others];active.remove(chosen);eliminations+=1
  assert not active and len(p['steps'])+len(fixed)==len(cards)
  for key,value in [('largest_bag_states',max_bag),('largest_separator_states',max_sep),('sum_bag_states',sum_bag),('sum_separator_states',sum_sep),('induced_width',width)]:assert p[key]==value and row[key]==value
  assert row['largest_64bit_cost_plus_argmin_payload_bytes']==16*max_sep and row['all_backpointer_64bit_payload_bytes']==8*sum_sep;rows.append({key:row[key] for key in ['case','initializer','timing_policy','priority','induced_width','largest_bag_states','largest_separator_states','sum_bag_states','largest_64bit_cost_plus_argmin_payload_bytes']});print(row['case'],row['initializer'],row['timing_policy'],row['priority'],'SYMBOLIC_BUCKET_PASS',flush=True)
 assert len(rows)==72
 files=[source,Path(__file__),D/'protocol.json'];(D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL72_INPUT_SCOPE_AND_SYMBOLIC_BUCKET_CARDINALITIES_INDEPENDENTLY_VERIFIED','rows':rows,'eliminations':eliminations,'bindings':{str(p):sha(p) for p in files},'target_payloads_read':False,'scope':'Specified min-fill ordering and dense-state cardinalities only; no optimal-width lower bound, numerical solve, elapsed performance or forecast gain proof.'},indent=2)+'\n');print('ALL72_SYMBOLIC_PROFILES_VERIFIED',eliminations)
if __name__=='__main__':main()
