"""Use the original accepted route's STA only, never candidate STA features."""
import json,re,time,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha,placements
root=Path(__file__).resolve().parents[1];source=root/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits';parent=root/'experiments/adder_tree_family_native_capture_v2_2026-10-06';receipt=json.loads((parent/'adder_tree_2L_032bits_receipt.json').read_text());assert all(sha(x['path'])==x['sha256'] for x in receipt['artifacts'].values());out=root/'experiments/native_baseline_critical_geometry_2026-10-06';out.mkdir();report=source/'report_timing.setup.rpt';protocol=root/'experiments/native_candidate_common_state_2026-10-06/protocol.json';pairs=json.loads(protocol.read_text())['pairs'];start=time.perf_counter();net=source/'design.net';place=placements(source/'design.place',sha(net));tree=ET.parse(net).getroot();atom_clb={};loc={}
for clb in tree.findall('block'):
 bid=place[clb.attrib['name']][4];loc[bid]=place[clb.attrib['name']][:2]
 for pb in clb.iter('block'):
  name=pb.attrib.get('name');
  if name and name!='open':
   assert name not in atom_clb or atom_clb[name]==bid;atom_clb[name]=bid
text=report.read_text().split('#Path 1\n',1)[1].split('data arrival time',1)[0];points=[]
for line in text.splitlines():
 m=re.match(r'^(.*?)\.([^\s.]+\[\d+\])\s+.*?\s(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',line)
 if m:
  atom,pin=m[1],m[2];assert atom in atom_clb;points.append({'atom':atom,'pin':pin,'block':atom_clb[atom],'incr_ns':float(m[3])})
connections=[];prev=None
for point in points:
 if point['pin'].startswith(('Q[','out[')):prev=point
 elif point['pin'].startswith(('in[','D[')) and prev is not None:
  if prev['block']!=point['block']:connections.append({'source_block':prev['block'],'sink_block':point['block'],'source_atom':prev['atom'],'sink_atom':point['atom'],'baseline_edge_ns':point['incr_ns']})
  prev=None
assert connections
features=[]
for i,(a,b) in enumerate(pairs):
 moved=loc.copy();moved[a],moved[b]=moved[b],moved[a]
 def length(l):return sum(abs(l[e['source_block']][0]-l[e['sink_block']][0])+abs(l[e['source_block']][1]-l[e['sink_block']][1]) for e in connections)
 delta=length(moved)-length(loc);features.append({'index':i,'pair':[a,b],'delta_critical_manhattan':delta,'selected':delta<0})
result={'connections':connections,'pairs':features,'wall_s':time.perf_counter()-start,'inputs_sha256':{str(p):sha(p) for p in (net,source/'design.place',report,protocol)},'source_sha256':sha(Path(__file__)),'rule':'Select strict reduction of summed CLB Manhattan distance along baseline Path 1.','scope':'Baseline prior native STA allowed; no candidate outcomes used in feature builder. Rounded report, top path only, geometry proxy not exact RC or guaranteed timing bound; previously studied design.'};(out/'features.json').write_text(json.dumps(result,indent=2)+'\n');print(len(connections),'critical cross-CLB edges;',sum(x['selected'] for x in features),'selected')
