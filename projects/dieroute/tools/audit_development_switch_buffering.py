"""Scan complete archived development RR switch and edge tables."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
sources={}
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 sources[str(p)]=h.hexdigest()
 return h.hexdigest()
base=root/'work/vpr_source_bound_initial_observation_build_20261015/source_vtr'
physical=base/'libs/libarchfpga/src/physical_types.cpp'
indexed=base/'libs/librrgraph/src/utils/alloc_and_load_rr_indexed_data.cpp'
assert 'return type == SwitchType::MUX' in physical.read_text()
text=indexed.read_text()
assert 'if (switches_buffered[RRIndexedDataId(cost_index)])' in text
assert 'T_quadratic = 0.;' in text
for p in [physical,indexed,Path(__file__).resolve()]:digest(p)
cases={}
for case in ['ex5p','diffeq','alu4']:
 p=root/f'work/native_{case}_stratix2die_cw80_20261013/rr_graph.xml'
 switches={};edges=Counter();nodes=Counter()
 for event,e in ET.iterparse(p,events=['end']):
  if e.tag=='switch':
   sid=int(e.attrib['id']);assert sid not in switches
   switches[sid]=dict(e.attrib)
  elif e.tag=='edge':edges[int(e.attrib['switch_id'])]+=1
  elif e.tag=='node':nodes[e.attrib['type']]+=1
  e.clear()
 assert edges and nodes and switches
 assert set(edges)<=set(switches)
 assert all(s['type']=='mux' for s in switches.values())
 cases[case]=dict(graph_sha256=digest(p),switches=switches,edge_switch_counts=dict(edges),node_types=dict(nodes),all_declared_and_referenced_switches_mux=True)
out=root/'work/development_switch_buffering_audit_20261015';out.mkdir(exist_ok=False)
(out/'audit.json').write_text(json.dumps(dict(status='three_complete_rr_graphs_use_only_mux_switches',cases=cases,source_sha256=sources,
 inference='All declared and edge-referenced switches are muxes. Frozen physical_types marks MUX buffered; frozen indexed-data code assigns exact zero T_quadratic in its buffered branch. This supports the zero echo observation and excludes unconditional sqrt(fanout) scaling as a faithful change for these graphs.',
 scope='Complete archived XML graphs plus source-level inference, not a new instrumented runtime, arbitrary architecture guarantee, full cost equivalence or QoR explanation.',research_complete=False,board_result=False),indent=2)+'\n')
print(json.dumps({k:dict(edges=sum(v['edge_switch_counts'].values()),switches=len(v['switches'])) for k,v in cases.items()}))
