"""Exhaustive finite-candidate conflict tree, independent of candidate generator."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_resource_avoidance_2026-10-06';r=json.loads((out/'receipt.json').read_text());import xml.etree.ElementTree as ET
xml=ET.parse(root/'work/nonzero_rc_fanout_observable64_2026-10-06/rr_graph.xml').getroot();caps={int(n.get('id')):int(n.get('capacity')) for n in xml.find('rr_nodes')};paths={tuple(c['key']):c['paths'] for c in r['candidates']};active={};states=0

def compatible(key,path):
 nets=defaultdict(set);incoming=defaultdict(set)
 for k,p in [*active.items(),(key,path)]:
  for n in p['nodes']:nets[n].add(k[0])
  for n,u,eid in p['parents']:incoming[(k[0],n)].add((u,eid))
 return all(len(v)<=caps[n] for n,v in nets.items()) and all(len(v)<=1 for v in incoming.values())
def prove():
 global states
 if len(active)==len(paths):return {'solution':True}
 states+=1
 if states>10000:raise RuntimeError('certificate state limit')
 possibilities={k:[i for i,p in enumerate(ps) if compatible(k,p)] for k,ps in paths.items() if k not in active};key=min(possibilities,key=lambda k:(len(possibilities[k]),k));options=possibilities[key]
 if not options:return {'dead_key':list(key)}
 children=[]
 for i in options:
  active[key]=paths[key][i];child=prove();del active[key]
  if child.get('solution'):return {'solution':True}
  children.append({'candidate':i,'proof':child})
 return {'key':list(key),'children':children}
certificate=prove();assert not certificate.get('solution');(out/'unsat_certificate.json').write_text(json.dumps({'certificate':certificate,'states':states,'receipt_sha256':sha(out/'receipt.json'),'scope':'Exhaustive finite candidate conflict tree; full graph feasibility remains established separately by native witness.'},indent=2)+'\n');print('certificate states',states)
