"""Distinguish native length from native indexed resource price, development only."""
import collections,hashlib,json,struct,xml.etree.ElementTree as E
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_zero_length_indexed_cost_profile_20261015'
def main():
 P.mkdir(exist_ok=False);refs={}
 def sha(f):
  key=str(f)
  if key not in refs:
   h=hashlib.sha256()
   with Path(f).open('rb') as stream:
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 protocol=json.loads((R/'work/rr_remaining_tail_precision_development_v2_20261015/protocol.json').read_text());outcomes=[]
 for case in protocol['cases']:
  label=case['label'];assert label in ['ex5p','diffeq','alu4']
  costs=R/'work'/('sb_native_indexed_costs_20261015/layers3_cw80' if label=='ex5p' else 'sb_development_native_indexed_costs_20261015/'+label)
  bound=json.loads((costs/'rebase_audit.json').read_text());rr=Path(case['native_case'])/'rr_graph.xml';assert sha(rr)==protocol['source_sha256'][str(rr)]
  base=costs/'costs/node_base_cost';assert sha(base)==bound['source_sha256'][str(base)]
  values=list(v[0] for v in struct.iter_unpack('<H',base.read_bytes()));categories=[None]*len(values);groups=collections.defaultdict(collections.Counter);nodes=0
  for _,el in E.iterparse(rr,events=['end']):
   if el.tag=='node':
    i=int(el.attrib['id']);assert i==nodes;nodes+=1;t=el.attrib['type'];loc=el.find('loc');segment=el.find('segment');seg=int(segment.attrib['segment_id']) if segment is not None else -1
    channel=t in ['CHANX','CHANY'];zero=channel and el.attrib.get('direction')=='NONE';span=0 if not channel or zero else 1+int(loc.attrib['xhigh'])-int(loc.attrib['xlow'])+int(loc.attrib['yhigh'])-int(loc.attrib['ylow'])
    category='zero_length_channel' if zero else 'directed_channel' if channel else 'terminal';categories[i]=category
    groups[(category,t,seg,span,values[i])]['nodes']+=1;el.clear()
   elif el.tag=='edge':el.clear()
  assert nodes==len(values)
  edges=Path(case['input_prefix']+'.edges');assert sha(edges)==bound['source_sha256'][str(edges)]
  counts=collections.Counter();positive_zero=0
  for dst,b,d in struct.iter_unpack('<IHH',edges.read_bytes()):
   assert dst<nodes and b==values[dst];counts[categories[dst]]+=1
   if categories[dst]=='zero_length_channel' and b>0:positive_zero+=1
  summarized=[]
  for (category,t,seg,span,b),v in sorted(groups.items()):summarized.append(dict(category=category,type=t,segment=seg,native_length=span,indexed_base_q=b,nodes=v['nodes']))
  zeros=[v for v in summarized if v['category']=='zero_length_channel'];outcomes.append(dict(case=label,nodes=nodes,zero_length_nodes=sum(v['nodes'] for v in zeros),positive_base_zero_length_nodes=sum(v['nodes'] for v in zeros if v['indexed_base_q']>0),incoming_edges_to_positive_base_zero_length_nodes=positive_zero,incoming_edges_by_category=dict(counts),classes=summarized))
  sha(costs/'rebase_audit.json');sha(costs/'costs/rr_indexed_data.echo')
 for f in [R/'work/rr_remaining_tail_precision_development_v2_20261015/protocol.json',R/'work/rr_remaining_layer_tail_variant_20261015/source/dieroute/src/rr_backend.cpp',Path(__file__).resolve()]:sha(f)
 report=dict(status='three_development_native_zero_length_and_indexed_prices_distinguished',outcomes=outcomes,source_sha256=refs,scope='Native node-length rule uses zero for DirectionNONE channels; native indexed resource prices are independently exported nominal segment-class costs. Every actual input edge base field checked against exported node price. Positive price for zero-length channels is not a conversion bug and must not be silently zeroed. This is no CPD/quality causality or new routing result.',adopted=False,board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps([{k:v for k,v in x.items() if k!='classes'} for x in outcomes]))
if __name__=='__main__':main()
