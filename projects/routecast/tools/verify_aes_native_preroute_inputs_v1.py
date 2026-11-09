"""Authenticate actual pack/place and graph-only stops, physical endpoint types and IDs."""
import sys,json,re,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from rr_graph import read_rr_graph
out=R/'experiments/aes_rr_graph_only_v1_2026-10-08';src=R/'experiments/aes_native_fixed_place_v1_2026-10-08';rp=out/'receipt.json';sp=src/'receipt.json';r=json.loads(rp.read_text());s=json.loads(sp.read_text());packp=json.loads((src/'protocol.json').read_text());bindings={**closure([Path(__file__)]),str(rp):sha(rp),str(sp):sha(sp)};rows=[]
for data in [r,s]:assert all(sha(k)==v for k,v in data['bindings'].items())
for row in r['rows']:
 name=row['name'];w=out/name;old=next(x for x in s['rows'] if x['name']==name);assert old['exit_code']==0 and row['status']=='GRAPH_AND_ENDPOINTS_CAPTURED';assert all(sha(k)==v for k,v in row['files'].items());assert all(sha(k)==v for k,v in old['files'].items())
 for f in ['design.blif','design.net','design.place']:assert sha(w/f)==sha(src/name/f)
 assert 'VPR succeeded' in (src/name/'pack_place.log').read_text();assert row['exit_code']==1 and not any(w.glob('*.route'));text=(w/'graph.log').read_text();assert 'missing.route' in text and 'VPR succeeded' not in text
 ep=json.loads((w/'endpoints.json').read_text());assert all(sha(x['path'])==x['sha256'] for x in ep['inputs'].values());g=read_rr_graph(w/'rr_graph.xml');assert g.sha256==ep['graph_sha256']==row['graph_sha256'];queries=ep['connections'];assert len(queries)==row['connections'] and {q['connection_id'] for q in queries}==set(range(len(queries)))
 for q in queries:
  assert q['source'] in g.nodes and q['sink'] in g.nodes and g.nodes[q['source']].type=='SOURCE' and g.nodes[q['sink']].type=='SINK';assert g.nodes[q['source']].capacity>0 and g.nodes[q['sink']].capacity>0;assert str(q['net_id']) in ep['net_names']
 net=ET.parse(w/'design.net').getroot();cmd=next(c['command'] for c in packp['cases'] if c['name']==name);assert net.get('architecture_id')=='SHA256:'+sha(cmd[1]) and net.get('atom_netlist_id')=='SHA256:'+sha(w/'design.blif')
 place=(w/'design.place').read_text();assert 'Netlist_ID: SHA256:'+sha(w/'design.net') in place
 rows.append({'name':name,'connections':len(queries),'nodes':len(g.nodes),'edges':len(g.edges),'pack_place_and_graph_only_inputs_pass':True});print(name,'PREROUTE PASS',len(queries),flush=True);del g
(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'originalHDL_actual_mapped_equivalence_proven':False,'native_route_labels_created':False,'scope':'Frozen mapped BLIF physical frontend only; originalHDL relation unproven and no final-routing/heldout claim.'},indent=2)+'\n')
