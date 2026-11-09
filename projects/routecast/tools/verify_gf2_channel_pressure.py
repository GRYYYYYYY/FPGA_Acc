"""OriginalXML successful-route audits and unrestricted failed-pair reachability."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,deque
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_channel_pressure_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and r['all_cases_retained'] and len(r['rows'])==9;assert sha(root/'tools/trial_gf2_channel_pressure.py')==p['source_sha256'];assert sha(p['cases'][0]['command'][0])==p['binary_sha256'] and sha(p['cases'][0]['command'][1])==p['architecture_sha256'];rows=[]
for c,row in zip(p['cases'],r['rows']):
 assert (c['data_width'],c['channels'])==(row['data_width'],row['channels']);assert all(sha(f)==h for f,h in row['files_sha256'].items());d=Path(c['cwd']);assert all(sha(d/n)==h for n,h in c['input_sha256'].items() if n!='design.place');text=(d/'run.log').read_text();graph=d/'rr_graph.xml';assert graph.exists();x=ET.parse(graph).getroot();nodes={int(n.get('id')):n for n in x.find('rr_nodes')};adj=defaultdict(list)
 for e in x.find('rr_edges'):adj[int(e.get('src_node'))].append(int(e.get('sink_node')))
 proof={'data_width':c['data_width'],'channels':c['channels'],'graph_sha256':sha(graph),'RR_nodes':len(nodes),'RR_edges':sum(map(len,adj.values()))}
 if row['FULL_success']:
  assert row['exit_code']==0 and all(t in text for t in ('RouterOpts.check_route: FULL','Completed routing consistency check successfully.','VPR succeeded'));a=audit(graph,d/'design.route');assert not a['overflow_units'];proof.update(classification='NATIVE_FULL_SUCCESS',connections=len(a['connections']),overflow_units=0,cpd_ns=row['cpd_ns'])
 elif row['timed_out']:proof.update(classification='TIMEOUT_UNRESOLVED')
 else:
  assert row['exit_code']!=0 and 'VPR failed to implement circuit' in text;matches=re.findall(r'Cannot route from[^\n]*SOURCE:(\d+)[^\n]*SINK:(\d+)',text);witnesses=[]
  if not matches:
   native=audit(graph,d/'design.route');overused=int(re.search(r'Total number of overused nodes: (\d+)',text)[1]);assert native['overflow_units']>0 and overused>0
   proof.update(classification='NATIVE_CONGESTION_FAILURE',connections=len(native['connections']),overflow_units=native['overflow_units'],reported_overused_nodes=overused)
   rows.append(proof);print(c['data_width'],c['channels'],proof['classification'],flush=True);continue
  for source,sink in matches:
   source=int(source);sink=int(sink);assert nodes[source].get('type')=='SOURCE' and nodes[sink].get('type')=='SINK';seen={source};queue=deque([source])
   while queue:
    n=queue.popleft()
    for dst in adj[n]:
     if dst not in seen:seen.add(dst);queue.append(dst)
   witnesses.append({'source':source,'sink':sink,'unrestricted_graph_reachable':sink in seen,'visited_nodes':len(seen)})
  proof.update(classification='STRUCTURAL_DISCONNECTION' if any(not w['unrestricted_graph_reachable'] for w in witnesses) else 'CONNECTED_NATIVE_SEARCH_FAILURE',witnesses=witnesses)
 rows.append(proof);print(proof['data_width'],proof['channels'],proof['classification'],flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'OriginalXML physical/zerooverflow route audit on successes; unrestricted directed reachability for concrete failed endpoints. Structural disconnect is not congestion label; connected failure is not proven globally unroutable. All cases preserved.'},indent=2)+'\n')
