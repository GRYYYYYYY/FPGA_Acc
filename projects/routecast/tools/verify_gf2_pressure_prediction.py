"""Independent partial-path/RC/union checks and failure interpretation."""
import json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,deque
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_pressure_prediction_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert sha(out/'protocol.json')==r['protocol_sha256'] and r['all_cases_retained'];assert all(sha(root/'tools'/n)==h for n,h in p['sources_sha256'].items());native=root/'experiments/gf2_channel_pressure_2026-10-06';nv=json.loads((native/'verification.json').read_text());nr=json.loads((native/'receipt.json').read_text());assert nv['receipt_sha256']==sha(native/'receipt.json');rows=[];matrix={'incomplete_native_failed':0,'incomplete_native_success':0,'complete_native_failed':0,'complete_native_success':0}
for c,row,nrow,nproof in zip(p['cases'],r['rows'],nr['rows'],nv['rows']):
 w=c['data_width'];channels=c['channels'];assert (w,channels)==(row['data_width'],row['channels'])==(nrow['data_width'],nrow['channels']);assert all(sha(f)==h for f,h in c['inputs_sha256'].items());d=out/f'gf2_d{w}_w{channels}';assert sha(d/'receipt.json')==row['candidate_sha256'] and sha(d/'endpoints.json')==row['endpoint_sha256'];q=json.loads((d/'receipt.json').read_text());ep=json.loads((d/'endpoints.json').read_text());assert len(q['records'])==q['completed_connections'] and len(ep['connections'])==q['required_connections']
 # Independent originalXML exactRC, no retained native exceptions for these candidates.
 src=(root/'tools/verify_tseng_selected_reference_import.py').read_text();check=src[src.index('def check('):src.index('inc=json.loads')];check=check.replace("len(snapshot['records'])==len(queries)==1234", "len(snapshot['records'])==snapshot['completed_connections']").replace("==set(queries)","<=set(queries)");tool=d/'audit.py';tool.write_text("import sys,json\nfrom pathlib import Path\nfrom collections import Counter,defaultdict\nfrom fractions import Fraction\nsys.path.insert(0,"+repr(str(root/'tools'))+")\nfrom immutable_xml_prediction_audit import ImmutableXMLAudit\nfrom buffered_rc_node_classes import read,arc_delay\n"+f"snapshot=json.loads(Path({str(d/'receipt.json')!r}).read_text());ep=json.loads(Path({str(d/'endpoints.json')!r}).read_text());graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)\n"+check+"check(snapshot,ep)\nassert all(Fraction(x['answer']['delay'],snapshot['scale'])<=Fraction(1,10**9) for x in snapshot['records'])\n")
 with (d/'audit.log').open('w') as f:code=subprocess.run(['python3',str(tool)],stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
 assert code==0
 failed=q['failure']['query'];assert failed in ep['connections'];graph=ep['inputs']['graph']['path'];xml=ET.parse(graph).getroot();adj=defaultdict(list)
 for e in xml.find('rr_edges'):adj[int(e.get('src_node'))].append(int(e.get('sink_node')))
 seen={failed['source']};todo=deque(seen)
 while todo:
  n=todo.popleft()
  for dst in adj[n]:
   if dst not in seen:seen.add(dst);todo.append(dst)
 reachable=failed['sink'] in seen
 own=set()
 edge_list=list(xml.find('rr_edges'))
 for rec in q['records']:
  if rec['net_id']==failed['net_id']:
   own.add(rec['source'])
   for eid in rec['answer']['physical_edge_ids']:own.add(int(edge_list[eid].get('sink_node')))
 capacities={int(n.get('id')):int(n.get('capacity')) for n in xml.find('rr_nodes')};ledger={int(n):v for n,v in q['ledger'].items()}
 def allowed(n):return ledger.get(n,0)-int(n in own)<capacities[n]
 available={failed['source']} if allowed(failed['source']) else set();queue=deque(available)
 while queue:
  n=queue.popleft()
  for dst in adj[n]:
   if dst not in available and allowed(dst):available.add(dst);queue.append(dst)
 constrained=failed['sink'] in available
 complete=q['completed_connections']==q['required_connections'];matrix[('complete' if complete else 'incomplete')+('_native_success' if nrow['FULL_success'] else '_native_failed')]+=1
 rows.append({'data_width':w,'channels':channels,'completed_connections':q['completed_connections'],'required_connections':q['required_connections'],'reported_failure':q['failure']['status'],'failed_query_unrestricted_reachable':reachable,'capacity_filtered_reachable':constrained,'failure_mechanism':'TOPOLOGY_DISCONNECTED' if not reachable else 'PRIOR_LEDGER_CAPACITY_BLOCKED' if not constrained else 'OTHER_SEARCH_RESTRICTION','native_classification':nproof['classification'],'partial_paths_independently_verified':True});print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'native_verification_sha256':sha(native/'verification.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'completion_vs_native_matrix':matrix,'scope':'Partial originalXML physical/exactRC/1ns/treeunion capacity and failure query unrestricted reachability verified. Incomplete predicate yields3native-success false alarms and6native-failure matches inoneposthocfamily; not calibrated classifier, full congestion-vector accuracy or global unrouteability proof.'},indent=2)+'\n')
