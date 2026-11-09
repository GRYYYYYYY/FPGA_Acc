"""Original XML edge-slot walk, exact objective and shared-parent audit."""
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
import json,hashlib,xml.parsers.expat as expat,time
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 begin=time.perf_counter();O=R/'experiments/mmc_NET5_current_criticality_attachment_v1_2026-10-19';proof=O/'verification.json';v=json.loads(proof.read_text());assert v['status']=='NET5_CURRENT_CRITICALITY_ZERO_CONGESTION_ALL41_MINIMUM_RAW_AND_BUDGET_PASS'
 for p,h in v['bindings'].items():assert sha(p)==h
 protocol=O/'protocol.json';spec=json.loads(protocol.read_text());output=O/'result.json';result=json.loads(output.read_text());queries=result['queries_in_execution_order'];assert result['complete'] and len(queries)==41;slots={s for q in queries for s in q['path_slots']};nodes={int(n) for n in result['arrival']};graph=Path(next(p for p in v['bindings'] if p.endswith('rr_graph.xml')));arcs={};costs={};caps={};kinds={};stack=[];edge=0;current_node=None;current_switch=None
 def start(tag,a):
  nonlocal current_node,current_switch,edge
  parent=stack[-1] if stack else None
  if tag=='switch' and parent=='switches':current_switch=int(a['id'])
  elif tag=='timing' and parent=='switch':
   value=Decimal(a.get('Tdel','0'))*Decimal(10)**18;assert value==value.to_integral_value();costs[current_switch]=int(value)
  elif tag=='node' and parent=='rr_nodes':
   current_node=int(a['id'])
   if current_node in nodes:caps[current_node]=int(a['capacity']);kinds[current_node]=a['type']
  elif tag=='timing' and parent=='node' and current_node in nodes:assert Decimal(a.get('R','0'))==Decimal(a.get('C','0'))==0
  elif tag=='edge' and parent=='rr_edges':
   if edge in slots:arcs[edge]=(int(a['src_node']),int(a['sink_node']),int(a['switch_id']))
   edge+=1
  stack.append(tag)
 def end(tag):assert stack.pop()==tag
 parser=expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end;tick=time.perf_counter()
 with graph.open('rb') as f:
  for chunk in iter(lambda:f.read(1<<20),b''):parser.Parse(chunk,False)
 parser.Parse(b'',True);xml_seconds=time.perf_counter()-tick;assert set(arcs)==slots and set(caps)==nodes and all(n>0 for n in caps.values());source=spec['source'];parents={};arrival={source:0};owned={source};seen=set();timing=R/'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19/episode_01/initial_connection_criticalities.json';criticalities={x['connection_id']:x for x in json.loads(timing.read_text())};pilot=R/'experiments/mmc_existing_marginal_attachment_pilot_v1_2026-10-19/protocol.json';old=json.loads(pilot.read_text());budgets={int(n):v for n,v in old['budgets'].items()};floors={int(n):v for n,v in old['floor_costs'].items()}
 assert [q['connection_id'] for q in queries]==spec['ordered_connection_ids']
 for r in queries:
  cid=r['connection_id'];assert cid not in seen;seen.add(cid);q=r['query'];c=criticalities[cid];value=Fraction(float(c['criticality_float32_text'])).limit_denominator(2**60)
  import struct
  f32=struct.unpack('<f',struct.pack('<f',float(c['criticality_float32_text'])))[0];numerator,denominator=f32.as_integer_ratio();assert r['criticality']==[numerator,denominator] and numerator>0;assert (q['net_id'],q['source'],q['sink'])==(c['net'],c['source_rr'],c['target_rr']);u=source;path_nodes=[u];raw=0;local=set()
  for slot in r['path_slots']:
   a,b,switch=arcs[slot];assert a==u and b not in local and b!=source;local.add(b)
   if b in parents:assert parents[b]==(u,slot)
   parents[b]=(u,slot);raw+=costs[switch];arrival[b]=raw;u=b;path_nodes.append(u)
  assert u==q['sink'] and kinds[u]=='SINK' and raw==r['raw']==floors[u]<=budgets[u] and r['committed'];assert r['objective_numerator']==numerator*raw and r['objective_denominator']==denominator
  attach=r['attach'];assert attach in owned and attach in path_nodes;position=path_nodes.index(attach);assert all(n in owned for n in path_nodes[:position+1]) and all(n not in owned for n in path_nodes[position+1:]);assert r['new_nodes']==len(path_nodes)-position-1;owned.update(path_nodes)
 assert parents=={int(n):tuple(x) for n,x in result['parents'].items()} and arrival=={int(n):x for n,x in result['arrival'].items()} and owned==nodes and len(seen)==41
 files=[proof,protocol,output,graph,timing,pilot,Path(__file__).resolve()];(O/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL41_ORIGINAL_XML_PATHS_PARENTS_BUDGETS_CRITICALITY_OBJECTIVES_AND_ATTACHMENTS_PASS','connections':41,'physical_edges':len(arcs),'unique_nodes':len(nodes),'XML_edges_scanned':edge,'xml_seconds':xml_seconds,'total_seconds_before_receipt':time.perf_counter()-begin,'bindings':{str(p):sha(p) for p in files},'scope':'Zero-congestion single-NET raw-floor control; no global capacity, predictive quality or speedup claim.'},indent=2)+'\n');print('CURRENT_CRITICALITY_NET5_XML_PASS',len(arcs),'edges',flush=True)
if __name__=='__main__':main()
