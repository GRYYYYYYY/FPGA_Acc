"""Canonical native terminal identity maps traced critical rootpins to selected paths."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_coupled_critical_rr_bindings_v2_2026-10-06';out.mkdir();tracefile=root/'experiments/ex5p_coupled_critical_packed_pins_v2_2026-10-06/receipt.json';trace=json.loads(tracefile.read_text());work=root/'work/ex5p_coupled_canonical_reload_2026-10-06/0/reload';identityfile=work/'identity.jsonl';route=work/'design.route';selectedfile=root/'experiments/ex5p_critical_coupled_2026-10-06/receipt.json';selected=json.loads(selectedfile.read_text());ep=json.loads((root/'experiments/ex5p_placement_swap_2026-10-06/endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path']);p={'inputs_sha256':{str(x):sha(x) for x in (tracefile,identityfile,route,selectedfile,graph)},'policy':'Canonical rootblock/port/bit→unique nativeNET/pin→terminal physicalpath→unique original selectedNETname/path. Preserve unresolved identities, no packedbit inference across sync.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');nets={x['name']:x for x in map(json.loads,identityfile.read_text().splitlines())};lookup=defaultdict(list)
for eid,e in enumerate(ET.parse(graph).getroot().find('rr_edges')):lookup[int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))].append(eid)
actual={};netid=None;prefix={};current=[];previous=None;switch=None
for line in route.read_text().splitlines():
 m=re.match(r'^\s*Net\s+(\d+)\s+\(',line)
 if m:netid=int(m[1]);prefix={};current=[];previous=None;switch=None;continue
 m=re.match(r'^Node:\s*(\d+).*?Switch:\s*(-?\d+)(?:\s+Net_pin_index:\s*(\d+))?',line)
 if not m:continue
 node=int(m[1])
 if node in prefix:current=prefix[node].copy()
 elif previous is not None and switch is not None and switch>=0:
  options=lookup[previous,node,switch];assert len(options)==1;current=current+[options[0]];prefix[node]=current.copy()
 else:current=[];prefix[node]=[]
 previous=node;switch=int(m[2])
 if m[3] is not None:key=(netid,int(m[3]));assert key not in actual;actual[key]=current.copy()
rows=[];unresolved=[]
for t in trace['bindings']:
 pin=t['external_cluster_input']
 if pin is None:unresolved.append(t);continue
 native=nets[t['resolved_net']];options=[p for p in native['pins'] if p['index']>0 and p['block']==pin['block'] and p['port']==pin['port'] and p['bit']==pin['physical_bit']];assert len(options)==1;path=actual[native['net_id'],options[0]['index']];matches=[r for r in selected['records'] if ep['net_names'][str(r['net_id'])]==t['resolved_net'] and r['answer']['physical_edge_ids']==path]
 if len(matches)!=1:unresolved.append({'trace':t,'matching_connection_ids':[r['connection_id'] for r in matches]});continue
 rec=matches[0];rows.append({'atom':t['atom'],'logical_bit':t['logical_bit'],'net_name':t['resolved_net'],'connection_id':rec['connection_id'],'net_id':rec['net_id'],'source':rec['source'],'sink':rec['sink'],'native_net_id':native['net_id'],'native_pin_index':options[0]['index'],'physical_edge_ids':path,'delay_integer':rec['answer']['delay'],'reported_arc_ns':t['timing_arc']['delay_ns']})
r={'bindings':rows,'unresolved':unresolved,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__)),'scope':'Critical logical arcs bound through canonicalpacked/nativepin/exactphysicalpath to originalselectedconnections. Report increment includes packed timing; not equated to RR branch delay.'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print('bound',len(rows),'unresolved',len(unresolved));print([(x['atom'],x['connection_id'],x['reported_arc_ns']) for x in rows])
