"""Explicit per-node indexed costs; never infer channel index from segment order.

Binding identity covers graph, decimal echo and native-export CSV bytes. The
caller must separately establish export provenance; hashes alone do not do so.
Only layer0 is supported. Ortho references may point to another segment;
they are checked for opposite direction and never used to infer node costs.
"""
import csv,io,hashlib
from decimal import Decimal,ROUND_HALF_UP
from fractions import Fraction
import xml.etree.ElementTree as ET
from compact_indexed_sketch import CompactIndexedSketch
from path_rc import PathRC,State

def digest(text):return hashlib.sha256(text.encode()).hexdigest()

def parse_bound_table(text):
 lines=text.splitlines()
 if len(lines)<3 or not lines[0].startswith('Delay normalization factor: ') or not lines[1].startswith('Cost Index'):raise ValueError('invalid table header')
 norm=Decimal(lines[0].split(':',1)[1].strip())
 if not norm.is_finite() or norm<=0:raise ValueError('invalid normalization')
 rows={}
 for line in lines[2:]:
  if not line.strip():continue
  fields=line.split()
  if len(fields)<9:raise ValueError('invalid row')
  i=int(fields[0]);kind=fields[1];name=' '.join(fields[2:-7]);base,ortho,seg,inv,linear,quadratic,load=fields[-7:]
  values=[Decimal(v) for v in (base,linear,quadratic,load)];inverse=Decimal(inv)
  if i<0 or i in rows or kind not in {'SOURCE','SINK','OPIN','IPIN','CHANX','CHANY'} or any(not v.is_finite() or v<0 for v in values):raise ValueError('invalid indexed cost')
  channel=kind in {'CHANX','CHANY'}
  if channel and (not name or not inverse.is_finite() or inverse<=0 or int(seg)<0):raise ValueError('invalid channel row')
  if not channel and (name or not inverse.is_nan() or int(seg)!=-1 or int(ortho)!=-1):raise ValueError('invalid terminal row')
  rows[i]={'type':kind,'name':name,'base':values[0],'segment':int(seg),'ortho':int(ortho),'inverse_length':inverse}
 if set(rows)!=set(range(len(rows))) or len(rows)<6:raise ValueError('invalid index coverage')
 for i,kind in enumerate(('SOURCE','SINK','OPIN','IPIN')):
  if rows[i]['type']!=kind:raise ValueError('invalid terminal index')
 for i,r in rows.items():
  if i<4:continue
  if r['type'] not in {'CHANX','CHANY'}:raise ValueError('nonchannel extended index')
  other=rows.get(r['ortho'])
  if other is None or other['type']!={'CHANX':'CHANY','CHANY':'CHANX'}[r['type']] :raise ValueError('unsupported orthogonal binding')
 return norm,rows

def validate_binding(graph,text,bindings_csv,identity):
 expected={'graph_sha256':graph.sha256,'table_sha256':digest(text),'bindings_sha256':digest(bindings_csv)}
 if any(identity.get(k)!=v for k,v in expected.items()):raise ValueError('binding identity mismatch')
 norm,rows=parse_bound_table(text);reader=csv.DictReader(io.StringIO(bindings_csv));indices={}
 if reader.fieldnames!=['node_id','cost_index','segment_index']:raise ValueError('invalid binding header')
 for record in reader:
  if set(record)!=set(reader.fieldnames) or any(v is None for v in record.values()):raise ValueError('invalid binding row')
  node,index,segment=(int(record[k]) for k in reader.fieldnames)
  if node in indices or node not in graph.nodes or index not in rows:raise ValueError('invalid node/index binding')
  n=graph.nodes[node];r=rows[index]
  if int(dict(n.location).get('layer','0'))!=0:raise ValueError('unsupported layer')
  if n.type!=r['type'] or segment!=r['segment']:raise ValueError('binding type/segment mismatch')
  if n.type in {'CHANX','CHANY'}:
   if n.segment_id!=segment or segment not in graph.segments or ET.fromstring(graph.segments[segment]).attrib.get('name')!=r['name']:raise ValueError('RR segment binding mismatch')
  indices[node]=index
 if set(indices)!=set(graph.nodes):raise ValueError('incomplete node bindings')
 return norm,rows,indices,expected

class BoundIndexedCost(CompactIndexedSketch):
 def __init__(self,graph,text,bindings_csv,identity,scale=10**6):
  if type(scale) is not int or scale<1:raise ValueError('invalid scale')
  norm,rows,indices,expected=validate_binding(graph,text,bindings_csv,identity)
  super().__init__(graph,'rr_length_switch',len(graph.nodes))
  self.indices=indices;self.rows=rows;self.normalization=Fraction(norm);self.scale=scale;self.identity=dict(expected)
  self.node_costs={n:int((rows[i]['base']/norm*scale).to_integral_value(rounding=ROUND_HALF_UP)) for n,i in indices.items()}
  self.outgoing={n:tuple((eid,dst,None if cost is None else self.node_costs[dst]) for eid,dst,cost in arcs) for n,arcs in self.outgoing.items()}

class BoundNormalizedRCBase(BoundIndexedCost):
 def __init__(self,graph,text,bindings_csv,identity,scale=10**6):
  super().__init__(graph,text,bindings_csv,identity,scale);rc=PathRC(graph)
  if any(not s[0] for s in rc.switches.values()):raise ValueError('nonbuffered graph requires resistance state')
  costs={}
  for eid,e in enumerate(graph.edges):
   delay=rc.step(State(Fraction(0),Fraction(0)),eid).delay
   if delay<0:raise ValueError('negative RC increment')
   base=Fraction(self.rows[self.indices[e.sink]]['base'])
   costs[eid]=round((delay+base)/self.normalization*scale/2)
  self.outgoing={n:tuple((eid,dst,None if w is None else costs[eid]) for eid,dst,w in arcs) for n,arcs in self.outgoing.items()}
