"""Native old aggregated interblock component versus original XML RR delay."""
import json,re,xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import import physical_paths
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_old_aggregated_timing_2026-10-06';maps=ROOT/'experiments/mux_old_timing_priority_2026-10-06';out=ROOT/'experiments/mux_old_interblock_rc_2026-10-06';out.mkdir();verification=json.loads((base/'verification.json').read_text());assert verification['receipt_sha256']==sha(base/'receipt.json');bindings={str(base/'verification.json'):sha(base/'verification.json')};rows=[]
for w in (8,16,32):
 work=base/f'w{w}/canonical';graph=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/rr_graph.xml';xml=ET.parse(graph).getroot();nodes={int(n.get('id')):n for n in xml.find('rr_nodes')};switches={int(s.get('id')):s for s in xml.find('switches')};route=work/'design.route';mapping=maps/f'w{w}_old.json';data=json.loads(mapping.read_text());table=work/'identity.jsonl';identity={r['name']:r for r in map(json.loads,table.read_text().splitlines())};pins={};name=None
 for line in route.read_text().splitlines():
  m=re.match(r'^Net\s+\d+\s+\((.*?)\)',line)
  if m:name=m[1];pins[name]=[]
  if re.search(r'Node:\s*\d+\s+SINK\b',line):pins[name].append(int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]))
 delays={}
 for name,paths in physical_paths(route).items():
  assert len(paths)==len(pins[name])
  for pin,path in zip(pins[name],paths):
   timing=nodes[path[0][0]].find('timing');delay=Fraction(timing.get('R'))*Fraction(timing.get('C'))/2
   for n,s in path[1:]:
    t=nodes[n].find('timing');st=switches[s].find('timing');assert switches[s].get('type')in('buffer','mux','tristate');delay+=(Fraction(st.get('R','0'))+Fraction(t.get('R'))/2)*Fraction(t.get('C'))+Fraction(st.get('Tdel','0'))
   delays[name,pin]=delay*10**9
 report=work/'report_timing.setup.rpt';bodies={int(n):body for n,body in re.findall(r'#Path (\d+)\n(.*?)(?=\n#Path |\Z)',report.read_text(),re.S)};samples=[]
 for path in data['paths']:
  body=bodies[path['rank']];inter=[Fraction(x)for x in re.findall(r'^\|\s+\(inter-block routing\)\s+([0-9.]+)',body,re.M)];external=[s for s in path['segments']if not s['internal']];assert len(inter)==len(external)
  for s,reported in zip(external,inter):
   net=identity[s['atom_net']];sink=[p for p in net['pins'][1:]if p['block']==s['native']['sink_cluster']];assert len(sink)==1;pin=sink[0]['index'];exact=delays[s['atom_net'],pin];delta=reported-exact
   samples.append(dict(rank=path['rank'],atom_net=s['atom_net'],sink_cluster=s['native']['sink_cluster'],sink_pin_index=pin,xml_rr_delay_ns=str(exact),native_interblock_ns=str(reported),difference_ns=float(delta),within_report_rounding=abs(delta)<=Fraction(1,2000)))
 file=out/f'w{w}.json';file.write_text(json.dumps(samples,indent=2)+'\n');rows.append(dict(width=w,samples=len(samples),outside_0_0005ns=sum(not s['within_report_rounding']for s in samples),maximum_absolute_difference_ns=max(abs(s['difference_ns'])for s in samples),samples_sha256=sha(file)))
 for p in (graph,route,mapping,table,report):bindings[str(p)]=sha(p)
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,scope='ExactFraction bufferedRR delay matched to native aggregated interblock delay using stable NET/sinkcluster identities; old layouts only. Report precision0.001ns, not globalSTA/architecture calibration.'),indent=2)+'\n');print(rows)
