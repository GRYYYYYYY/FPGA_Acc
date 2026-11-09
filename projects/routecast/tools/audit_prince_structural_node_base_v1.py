"""Rebuild node costs independently from original XML and float32 bit fields."""
import json,struct,xml.etree.ElementTree as E
from pathlib import Path
from fractions import Fraction
from array import array
from pre_route_endpoints import sha

def audit(graph,proof_path,scale):
 proof_path=Path(proof_path);v=json.loads(proof_path.read_text());assert v['scale']==scale and all(sha(p)==h for p,h in v['bindings'].items())
 table=next(Path(p) for p in v['bindings'] if p.endswith('/indexed.tsv'))
 rows=[line.split() for line in table.read_text().splitlines()];indexed={int(x[1]):x for x in rows if x[0]=='I'};types=['SOURCE','SINK','IPIN','OPIN','CHANX','CHANY'];mapping={}
 for x in rows:
  if x[0]!='N':continue
  kind,index=int(x[1]),int(x[2]);r=indexed[index];bits=int.from_bytes(struct.pack('!f',float(r[3])),'big');exponent=(bits>>23)&255;mantissa=bits&((1<<23)-1)
  assert not bits>>31 and exponent!=255
  if exponent:mantissa+=1<<23;power=exponent-150
  else:power=-149
  exact=Fraction(mantissa)*(Fraction(2)**power);scaled=exact*scale;base=-(-scaled.numerator//scaled.denominator)
  assert base-1<scaled<=base;key=(types[kind],int(r[2]));assert key not in mapping;mapping[key]=base
 values=array('Q');stack=[]
 for event,node in E.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(node);continue
  if node.tag=='node':
   assert int(node.get('id'))==len(values);seg=node.find('segment');key=(node.get('type'),int(seg.get('segment_id')) if seg is not None else -1);values.append(mapping[key]);stack[-2].remove(node);node.clear()
  if node.tag=='rr_nodes':break
  stack.pop()
 original=array('Q');original.frombytes((proof_path.parent/'node_base.u64').read_bytes());assert values==original and len(values)==v['nodes']
 digest=sha(graph);assert digest==v['graph_sha256'];assert any(h==digest and Path(p).suffix=='.xml' for p,h in v['bindings'].items())
 return tuple(values)
