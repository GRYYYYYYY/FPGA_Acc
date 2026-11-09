"""Recompute RR delay directly from XML Fractions without IntegerRC."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from native_route_ledger_import import physical_paths
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_sta_rc_alignment_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['bindings'].items());assert r['source_sha256']==sha(ROOT/'tools/diagnose_mux_sta_rc_alignment.py');checked=0
for w in (8,16,32):
 graph=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/rr_graph.xml';xml=ET.parse(graph).getroot();nodes={int(n.get('id')):n for n in xml.find('rr_nodes')};switches={int(s.get('id')):s for s in xml.find('switches')}
 for mode in ('candidate','reference'):
  work=ROOT/(f'experiments/mux_candidate_timing_reports_v2_2026-10-06/w{w}/canonical'if mode=='candidate'else f'experiments/mux_budget_repair_quality_gate_2026-10-06/w{w}/canonical');route=work/'design.route';pins={};name=None
  for line in route.read_text().splitlines():
   m=re.match(r'^Net\s+\d+\s+\((.*?)\)',line)
   if m:name=m[1];pins[name]=[]
   if re.search(r'Node:\s*\d+\s+SINK\b',line):pins[name].append(int(re.search(r'Net_pin_index:\s*(\d+)',line)[1]))
  values={}
  for name,paths in physical_paths(route).items():
   for pin,path in zip(pins[name],paths):
    timing=nodes[path[0][0]].find('timing');delay=Fraction(timing.get('R'))*Fraction(timing.get('C'))/2
    for n,s in path[1:]:
     t=nodes[n].find('timing');st=switches[s].find('timing');assert switches[s].get('type')in('buffer','mux','tristate');delay+=(Fraction(st.get('R','0'))+Fraction(t.get('R'))/2)*Fraction(t.get('C'))+Fraction(st.get('Tdel','0'))
    values[name,pin]=float(delay*10**9)
  p=out/f'w{w}_{mode}.json';summary=next(x for x in r['rows']if x['width']==w and x['mode']==mode);assert sha(p)==summary['samples_sha256'];samples=json.loads(p.read_text());assert len(samples)==summary['samples']
  for s in samples:
   assert abs(values[s['atom_net'],s['sink_pin_index']]-s['rr_path_ns'])<1e-12;assert abs(s['sta_increment_ns']-s['rr_path_ns']-s['residual_ns'])<1e-12;checked+=1
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),sample_count=checked,exact_fraction_original_xml_recomputed=True,scope='Independent XML delay formula verifies RR estimates, not local timing decomposition or causal model error.'),indent=2)+'\n');print(checked)
