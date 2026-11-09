"""Explicit full native timing-edge to clustered physical RR branch mapping."""
import json,re,xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import import physical_paths
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06';identityroot=ROOT/'experiments/mux_atom_timing_identity_2026-10-06';out=ROOT/'experiments/mux_full_timing_rr_2026-10-06';out.mkdir();bindings={};rows=[]
for w in (8,16,32):
 work=base/f'w{w}/canonical';tgpath=base/f'w{w}_timing_graph.json';tg=json.loads(tgpath.read_text());atable=identityroot/f'w{w}/atom_identity.jsonl';atom={}
 for a in map(json.loads,atable.read_text().splitlines()):
  if a['node_id']is not None:
   n=a['node_id'];assert n not in atom or atom[n]['atom_pin_id']==a['atom_pin_id'];atom[n]=a
 table=work/'identity.jsonl';nets={x['name']:x for x in map(json.loads,table.read_text().splitlines())};route=work/'design.route';pins={};name=None
 for line in route.read_text().splitlines():
  m=re.match(r'^Net\s+\d+\s+\((.*?)\)',line)
  if m:name=m[1];pins[name]=[]
  if re.search(r'Node:\s*\d+\s+SINK\b',line):pins[name].append(int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]))
 graph=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/rr_graph.xml';xml=ET.parse(graph).getroot();nodes={int(n.get('id')):n for n in xml.find('rr_nodes')};switches={int(s.get('id')):s for s in xml.find('switches')};branches={}
 for name,paths in physical_paths(route).items():
  assert len(paths)==len(pins[name])
  for pin,path in zip(pins[name],paths):
   t=nodes[path[0][0]].find('timing');value=Fraction(t.get('R'))*Fraction(t.get('C'))/2
   for n,s in path[1:]:
    t=nodes[n].find('timing');st=switches[s].find('timing');assert switches[s].get('type')in('buffer','mux','tristate');value+=(Fraction(st.get('R','0'))+Fraction(t.get('R'))/2)*Fraction(t.get('C'))+Fraction(st.get('Tdel','0'))
   branches[name,pin]=dict(rr_delay_seconds=str(value),source=path[0][0],sink=path[-1][0])
 mapped={};internal=0;used=set()
 for eid,e in tg['edges'].items():
  if e['type']!='INTERCONNECT':continue
  u,v=atom[e['source']],atom[e['sink']];assert u['net']==v['net']
  if u['cluster']==v['cluster']:internal+=1;continue
  native=nets[u['net']];assert native['pins'][0]['block']==u['cluster'];options=[p for p in native['pins'][1:]if p['block']==v['cluster']];assert len(options)==1;pin=options[0];branch=branches[u['net'],pin['index']];loc=nodes[branch['sink']].find('loc');assert tuple(int(loc.get(k,'0'))for k in('xlow','ylow','layer','ptc'))==tuple(pin[k]for k in('x','y','layer','class'));offset=Fraction(e['max_delay_seconds'])-Fraction(branch['rr_delay_seconds']);assert offset>=0;used.add((u['net'],pin['index']));mapped[eid]=dict(atom_net=u['net'],source_atom=u['atom'],sink_atom=v['atom'],source_cluster=u['cluster'],sink_cluster=v['cluster'],native_net_id=native['net_id'],sink_pin_index=pin['index'],branch=branch,old_local_offset_seconds=str(offset))
 assert used==set(branches)
 file=out/f'w{w}.json';file.write_text(json.dumps(dict(timing_graph_sha256=sha(tgpath),external_edges=mapped,internal_interconnect_edges=internal,scope='Localoffset includes oldpacking/intracluster effects and echo rounding; carry-forward is hypothesis, not invariant after move.'),indent=2)+'\n');rows.append(dict(width=w,external_timing_edges=len(mapped),internal_interconnect_edges=internal,unique_native_connections=len(used),mapping_sha256=sha(file)));print(rows[-1],flush=True)
 for p in(tgpath,atable,table,route,graph):bindings[str(p)]=sha(p)
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,scope='FullnativeAtomLookup-to-clusterNET/sinkclass-to-RR branch join; all3331physicalconnections covered, multiple atomedges may shareone clusteredconnection.'),indent=2)+'\n')
