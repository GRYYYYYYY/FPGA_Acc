"""Independent archived accepted-ledger XML/RC/NET-union/native evidence audit."""
import json,re
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha,placements
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from stream_native_route_audit import audit
from audit_native_route import NODE
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_native_seeded_owner_advance_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(root/'tools'/n)==h for n,h in p['sources_sha256'].items());assert [c['width'] for c in p['cases']]==[x['width'] for x in r['rows']]==[32,64,128]
def native_paths(path):
 result={};parents={};previous=None;switch=None;name=None
 for line in path.read_text().splitlines():
  if line.startswith('Net '):
   name=line.split('(',1)[1].split(')',1)[0];assert name not in result;result[name]=[];parents={};previous=None;switch=None;continue
  m=NODE.match(line)
  if not m:continue
  n=int(m[1]);kind=m[2]
  if kind=='SOURCE':parents[n]=[(n,None)]
  elif kind=='SINK':assert previous in parents;result[name].append(tuple(parents[previous]+[(n,switch)]))
  elif n not in parents:assert previous in parents;parents[n]=parents[previous]+[(n,switch)]
  previous=n;switch=int(m[3])
 return {n:sorted(v) for n,v in result.items() if v}
rows=[]
for case,row in zip(p['cases'],r['rows']):
 w=row['width'];assert all(sha(f)==h for f,h in case['bindings'].items());file=out/f'gf2_d{w}_accepted.json';assert sha(file)==row['snapshot_sha256'];s=json.loads(file.read_text());ep=json.loads((root/f'experiments/gf2_d{w}_placement_swap_2026-10-06/endpoints.json').read_text());assert s['endpoint_metadata']==ep and s['revision']==row['revision']==1;assert all(sha(x['path'])==x['sha256'] for x in ep['inputs'].values());graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph);scale=json.loads((root/f'experiments/gf2_native_seeded_updates_2026-10-06/gf2_d{w}/receipt.json').read_text())['scale'];queries={q['connection_id']:q for q in ep['connections']};assert len(s['records'])==len(queries)==row['connections'];unions=defaultdict(set);parents=defaultdict(dict);ledger=Counter();paths=defaultdict(list);seen=set()
 for rec in s['records']:
  cid=rec['connection_id'];assert cid not in seen;seen.add(cid);q=queries[cid];assert all(rec[k]==v for k,v in q.items());n=q['source'];used={n};res,cap=classes[ids[n]];delay=res*cap/2;path=[(n,None)];net=q['net_id']
  for eid in rec['answer']['physical_edge_ids']:
   edge=xml.graph.edges[eid];assert edge.source==n and edge.sink not in used;n=edge.sink;used.add(n);delay+=arc_delay(classes,switches,ids[n],edge.switch_id);path.append((n,edge.switch_id));parent=(edge.source,eid);assert n not in parents[net] or parents[net][n]==parent;parents[net][n]=parent
  assert n==q['sink'] and delay==Fraction(rec['answer']['delay'],scale);ledger.update(used-unions[net]);unions[net].update(used);paths[ep['net_names'][str(net)]].append(tuple(path))
 assert dict(ledger)=={int(n):v for n,v in s['ledger'].items()} and all(v<=xml.caps[n] for n,v in ledger.items())
 selection=json.loads(Path(case['selection']).read_text());v=json.loads(Path(case['verification']).read_text());assert v['selection_sha256']==sha(case['selection']) and v['FULL_reload_success'];assert selection['selected']==row['selected']==('predicted' if selection['predicted_cpd_ns']<=selection['reference_cpd_ns'] else 'reference');assert all(sha(f)==h for f,h in selection['files_sha256'].items());route=next(Path(f) for f in selection['files_sha256'] if Path(f).name=='design.route');assert {n:sorted(v) for n,v in paths.items()}==native_paths(route);native=audit(graph,route);assert not native['overflow_units'] and dict(ledger)=={int(n):c for n,c in native['node_occupancy'].items()};bundle=route.parent;log=(bundle/'reload.log').read_text()
 for text in ('RouterOpts.check_route: FULL','Completed routing consistency check successfully.','VPR succeeded'):assert text in log
 assert float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1])==row['selected_cpd_ns']
 for pattern in (r'Found (\d+) mismatches',r'Fixed (\d+) routing traces'):assert int(re.search(pattern,log)[1])==0
 assert {n:v[:4] for n,v in placements(bundle/'design.place',sha(bundle/'design.net')).items()}=={n:v[:4] for n,v in placements(Path(ep['inputs']['place']['path']),ep['inputs']['net']['sha256']).items()}
 rows.append({'width':w,'connections':len(seen),'selected':row['selected'],'all_RC_delays_exact':True,'native_paths_and_occupancy_exact':True,'overflow_units':0,'multi_parent_nodes':0,'revision':1});print(w,'archived owner independently verified',flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'source_sha256':sha(Path(__file__)),'rows':rows,'scope':'Independent archived owner full endpoints/originalXML RC/unioncapacity/parents and selected native physical paths/occupancy/FULL/timing/placement checked. In-process stale/consumed guards are producer assertions; no concurrent/durable recovery or complete timing-cost coverage.'},indent=2)+'\n')
