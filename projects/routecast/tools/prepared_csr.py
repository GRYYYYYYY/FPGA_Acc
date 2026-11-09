"""Versioned little-endian independent additive RR transport, not a kernel.

No inference/remapping of physical resources: CSR ranks retain raw node IDs,
raw edge IDs and switch IDs. UINT64_MAX marks disabled cost/absent segment.
Tree-prefix exact RC state and congestion updates are outside this v1 schema.
"""
import json,hashlib,sys
from array import array
from pathlib import Path
U64=(1<<64)-1
TYPES={s:i for i,s in enumerate(('SOURCE','SINK','OPIN','IPIN','CHANX','CHANY'))}
DIRECTIONS={s:i for i,s in enumerate(('NONE','INC_DIR','DEC_DIR','BI_DIR'))}
LEGACY_SIDES={s:i for i,s in enumerate(('NONE','LEFT','RIGHT','TOP','BOTTOM'))}
# Append VPR XSD multi-side values; existing byte codes remain unchanged.
SIDES={**LEGACY_SIDES,**{s:i+5 for i,s in enumerate(('RIGHT_LEFT','RIGHT_BOTTOM','RIGHT_BOTTOM_LEFT','TOP_RIGHT','TOP_BOTTOM','TOP_LEFT','TOP_RIGHT_BOTTOM','TOP_RIGHT_LEFT','TOP_BOTTOM_LEFT','TOP_RIGHT_BOTTOM_LEFT','BOTTOM_LEFT'))}}
def side_codes(values):
 return SIDES if any(v>=5 for v in values) else LEGACY_SIDES

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(engine,out):
 out=Path(out)
 if out.exists():raise ValueError('fresh output required')
 g=engine.graph;ids=sorted(g.nodes);rank={n:i for i,n in enumerate(ids)};fields={};kinds={};seen=bytearray(len(g.edges));seen_count=0
 def field(name,values,kind='Q'):
  fields[name]=values if isinstance(values,array) and values.typecode==kind else array(kind,values);kinds[name]=kind
 field('node_ids',ids);field('row_offsets',[0]);edge_ids=array('Q');dsts=array('Q');switches=array('Q');costs=array('Q')
 for n in ids:
  for eid,dst,w in engine.outgoing[n]:
   if type(eid) is not int or not 0<=eid<len(g.edges) or seen[eid]:raise ValueError('invalid/duplicate raw edge')
   e=g.edges[eid]
   if e.source!=n or e.sink!=dst or dst not in rank:raise ValueError('CSR topology mismatch')
   if w is not None and (type(w) is not int or not 0<=w<U64):raise ValueError('invalid cost')
   seen[eid]=1;seen_count+=1;edge_ids.append(eid);dsts.append(rank[dst]);switches.append(e.switch_id);costs.append(U64 if w is None else w)
  fields['row_offsets'].append(len(edge_ids))
 if seen_count!=len(g.edges):raise ValueError('incomplete physical edge coverage')
 for name,values in (('edge_ids',edge_ids),('dest_ranks',dsts),('switch_ids',switches),('costs',costs)):field(name,values)
 records=[g.nodes[n] for n in ids];locations=[dict(n.location) for n in records]
 field('types',(TYPES[n.type] for n in records),'B');field('directions',(DIRECTIONS[n.direction] for n in records),'B');field('sides',(SIDES[l.get('side','NONE')] for l in locations),'B');field('capacities',(n.capacity for n in records));field('segments',(U64 if n.segment_id is None else n.segment_id for n in records))
 for name in ('xlow','xhigh','ylow','yhigh','layer','ptc'):field(name,(int(l.get(name,'0')) for l in locations),'q')
 out.mkdir();files={}
 for name,data in fields.items():
  if sys.byteorder!='little':data.byteswap()
  file=out/(name+'.bin');file.write_bytes(data.tobytes());files[name]={'file':file.name,'type':kinds[name],'elements':len(data),'bytes':file.stat().st_size,'sha256':sha(file)}
 context={'graph_sha256':g.sha256,'cost_identity':getattr(engine,'identity',{}),'scale':getattr(engine,'scale',None),'normalization':str(getattr(engine,'normalization','unspecified')),'mode':getattr(engine,'mode','explicit'),'cost_payload_sha256':files['costs']['sha256'],'edge_mapping_sha256':files['edge_ids']['sha256']}
 manifest={'schema':'ROUTECAST_PREPARED_ADDITIVE_CSR_V1','byteorder':'little','nodes':len(ids),'edges':len(edge_ids),'disabled_cost_sentinel':U64,'context':context,'context_sha256':hashlib.sha256(json.dumps(context,sort_keys=True).encode()).hexdigest(),'type_codes':TYPES,'direction_codes':DIRECTIONS,'side_codes':side_codes(fields['sides']),'files':files,'scope':'independent additive search transport; no RC tree prefix, epochs or dynamic pressure representation'};(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest

def read(out,graph_sha256,expected_context_sha256=None):
 out=Path(out);m=json.loads((out/'manifest.json').read_text())
 if m['schema']!='ROUTECAST_PREPARED_ADDITIVE_CSR_V1' or m['byteorder']!='little' or m['context']['graph_sha256']!=graph_sha256:raise ValueError('transport identity mismatch')
 context_sha=hashlib.sha256(json.dumps(m['context'],sort_keys=True).encode()).hexdigest()
 if context_sha!=m['context_sha256'] or (expected_context_sha256 is not None and context_sha!=expected_context_sha256):raise ValueError('cost context mismatch')
 fields={}
 for name,f in m['files'].items():
  path=out/f['file']
  if path.parent!=out or sha(path)!=f['sha256']:raise ValueError('transport payload mismatch')
  data=array(f['type']);data.frombytes(path.read_bytes())
  if sys.byteorder!='little':data.byteswap()
  if len(data)!=f['elements'] or path.stat().st_size!=f['bytes']:raise ValueError('payload length mismatch')
  fields[name]=data
 n=m['nodes'];e=m['edges'];rows=fields['row_offsets']
 for name in ('types','directions','sides','capacities','segments','xlow','xhigh','ylow','yhigh','layer','ptc'):
  if name not in fields or len(fields[name])!=n:raise ValueError('invalid node payload length')
 if m.get('side_codes') not in (LEGACY_SIDES,SIDES) or any(v not in m['side_codes'].values() for v in fields['sides']):raise ValueError('side code mapping mismatch')
 if any(v not in TYPES.values() for v in fields['types']) or any(v not in DIRECTIONS.values() for v in fields['directions']) or any(v not in SIDES.values() for v in fields['sides']):raise ValueError('invalid node enum')
 if len(fields['node_ids'])!=n or len(set(fields['node_ids']))!=n or len(rows)!=n+1 or rows[0]!=0 or rows[-1]!=e or any(a>b for a,b in zip(rows,rows[1:])):raise ValueError('invalid CSR rows')
 for name in ('edge_ids','dest_ranks','switch_ids','costs'):
  if len(fields[name])!=e:raise ValueError('invalid edge payload length')
 seen=bytearray(e)
 for eid in fields['edge_ids']:
  if eid>=e or seen[eid]:raise ValueError('invalid edge mapping')
  seen[eid]=1
 if any(d>=n for d in fields['dest_ranks']):raise ValueError('invalid destination rank')
 if m['context']['cost_payload_sha256']!=m['files']['costs']['sha256'] or m['context']['edge_mapping_sha256']!=m['files']['edge_ids']['sha256']:raise ValueError('inconsistent cost context')
 return m,fields

def arcs(fields,raw_source):
 rank={n:i for i,n in enumerate(fields['node_ids'])}[raw_source]
 for i in range(fields['row_offsets'][rank],fields['row_offsets'][rank+1]):
  w=fields['costs'][i];yield fields['edge_ids'][i],fields['node_ids'][fields['dest_ranks'][i]],None if w==U64 else w
