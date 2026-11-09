"""Original XML channel geometry: per-path penalty versus perNET wire union."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
ROOT=Path(__file__).resolve().parents[1];weighted=ROOT/'experiments/mux_wire_penalty_fixed_cap_cohort_2026-10-07';plain=ROOT/'experiments/mux_fixed_connection_cap_cohort_2026-10-07';cold=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06';p=json.loads((weighted/'protocol.json').read_text());cr=json.loads((cold/'receipt.json').read_text());assert json.loads((cold/'verification.json').read_text())['receipt_sha256']==sha(cold/'receipt.json');rows=[];bindings={str(cold/'receipt.json'):sha(cold/'receipt.json')};last=None
for case in p['cases']:
 w,i=case['width'],case['index'];wf=weighted/f'w{w}_m{i}/result.json'
 if not wf.exists():continue
 ep=json.loads(Path(case['target']).read_text());graph=ep['inputs']['graph']['path']
 if w!=last:
  xml=ImmutableXMLAudit(graph,ep['graph_sha256']);lengths={}
  for event,node in ET.iterparse(graph,events=('end',)):
   if node.tag=='node':
    loc=node.find('loc');kind=node.get('type');length=(int(loc.get('xhigh'))-int(loc.get('xlow'))+1) if kind=='CHANX' else ((int(loc.get('yhigh'))-int(loc.get('ylow'))+1) if kind=='CHANY' else 0);lengths[int(node.get('id'))]=length;node.clear()
  last=w
 def measure(records):
  unions=defaultdict(set);path_sum=0
  for r in records:
   nodes={r['source']};u=r['source']
   for eid in r['answer']['physical_edge_ids']:
    e=xml.graph.edges[eid];assert e.source==u;u=e.sink;nodes.add(u)
   assert u==r['sink'];path_sum+=sum(lengths[n] for n in nodes);unions[r['net_id']].update(nodes)
  bynet={net:sum(lengths[n] for n in nodes) for net,nodes in unions.items()}
  return dict(unique_wirelength=sum(bynet.values()),path_wirelength_sum=path_sum,duplicate_shared_wire_units=path_sum-sum(bynet.values()),net_wirelength=bynet)
 pf=plain/f'w{w}_m{i}/result.json';cf=cold/f'mux_w{w}_m{i}_0/accepted_state.json';wr=json.loads(wf.read_text());pr=json.loads(pf.read_text());cs=json.loads(cf.read_text());cold_row=next(r for r in cr['rows'] if (r['width'],r['index'])==(w,i));assert sha(cf)==cold_row['rounds'][0]['snapshot_sha256'];values=dict(plain=measure(pr['result']['candidate']['records']),weighted=measure(wr['result']['candidate']['records']),cold=measure(cs['records']));log=next(Path(f) for f in cold_row['rounds'][0]['reload']['files'] if f.endswith('/reload.log'));assert sha(log)==cold_row['rounds'][0]['reload']['files'][str(log)];native_wire=int(re.findall(r'Total wirelength:\s*(\d+)',log.read_text())[-1]);assert values['cold']['unique_wirelength']==native_wire
  # Every path's shared prefix is charged repeatedly by the static edge term.
 delta=values['weighted']['unique_wirelength']-values['plain']['unique_wirelength'];rows.append(dict(width=w,index=i,values=values,weighted_minus_plain_unique_wire=delta,weighted_minus_cold_unique_wire=values['weighted']['unique_wirelength']-native_wire,largest_net_deltas=sorted([dict(net_id=n,wire_delta=values['weighted']['net_wirelength'].get(n,0)-v) for n,v in values['plain']['net_wirelength'].items()],key=lambda x:(-abs(x['wire_delta']),x['net_id']))[:10]));
 for f in (wf,pf,cf,log,Path(case['target'])):bindings[str(f)]=sha(f)
out=ROOT/'experiments/mux_wire_union_objective_diagnosis_2026-10-07';out.mkdir(exist_ok=True);(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,scope='Original XML perNET channel-node union versus sum over connection paths. Cold unions equal authenticated native wirelength logs; weighted/plain candidate physical proofs separate. Static destination-span penalty double charges shared prefixes across queries and is not the unique NET-tree objective. Retrospective diagnostic, no new routing/native acceptance/time claim.'),indent=2)+'\n');print([(r['width'],r['index'],r['weighted_minus_plain_unique_wire'],r['weighted_minus_cold_unique_wire']) for r in rows],flush=True)
