"""Crosscheck mapped external segments against packed inputs and route pin records."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_timing_net_mapping_v2_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['bindings'].items());assert r['source_sha256']==sha(ROOT/'tools/map_mux_timing_nets_v2.py');rows=[]
for summary in r['rows']:
 w=summary['width'];mode=summary['mode'];p=out/f'w{w}_{mode}.json';data=json.loads(p.read_text());work=ROOT/(f'experiments/mux_candidate_timing_reports_v2_2026-10-06/w{w}/canonical'if mode=='candidate'else f'experiments/mux_budget_repair_quality_gate_2026-10-06/w{w}/canonical')
 blocks={b.get('name'):b for b in ET.parse(work/'design.net').getroot().findall('block')};pins=set();net=None
 for line in (work/'design.route').read_text().splitlines():
  m=re.match(r'^Net\s+(\d+)\s+\((.*?)\)',line)
  if m:net=(int(m[1]),m[2])
  if re.search(r'Node:\s*\d+\s+SINK\b',line):pins.add((*net,int(re.search(r'Net_pin_index:\s*(\d+)',line)[1])))
 count=0
 for path in data['paths']:
  for s in path['segments']:
   if s['internal']:assert s['native']is None;continue
   n=s['native'];assert (n['net_id'],s['atom_net'],n['sink_pin_index'])in pins
   b=blocks[n['sink_cluster']];tokens=[token for port in b.findall('./inputs/port')for token in (port.text or '').split()];assert s['atom_net']in tokens
   assert any(x.get('name')==s['sink_atom']for x in b.iter('block'));assert any(x.get('name')==s['source_atom']for x in blocks[n['source_cluster']].iter('block'));count+=1
 rows.append(dict(width=w,mode=mode,external_segments_crosschecked=count,mapping_sha256=sha(p),route_sha256=sha(work/'design.route')))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Externalsegments independently present in packedcluster inputsignal and nativeNET sinkpin records; internal atom arcs are BLIF mapping only. No causal timing attribution or criticality prediction claimed.'),indent=2)+'\n');print(rows)
