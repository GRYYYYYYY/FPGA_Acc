"""Classify actual attachment receipts by archived native RR node type."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
graph=root/'work/native_ex5p_stratix2die_cw80_20261013/rr_graph.xml'
types={}
for event,e in ET.iterparse(graph,events=['end']):
 if e.tag=='node':types[int(e.attrib['id'])]=e.attrib['type']
 e.clear()
paths={a:root/f'work/rr_fanout_net_order_variant_20261015/native_runs/{a}_0/route.attachments.csv' for a in ['legacy_bulk','fanout_bulk','legacy_serial','fanout_serial']}
paths['fanout_serial_weight256_first']=root/'work/rr_fanout_seed_weight_variant_v2_20261015/native_runs/weight256_0/route.attachments.csv'
results={};sources={str(graph):hashlib.sha256(graph.read_bytes()).hexdigest()}
for label,path in paths.items():
 counts=Counter();examples=[];total=0
 with path.open() as stream:
  for row in csv.DictReader(stream):
   kind=types[int(row['attachment'])];counts[kind]+=1;total+=1
   if kind in ['IPIN','SINK'] and len(examples)<8:examples.append(row)
 results[label]=dict(attachments=total,types=dict(counts),terminal_attachment_examples=examples)
 sources[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
source=root/'work/vpr_source_bound_initial_observation_build_20261015/source_vtr/vpr/src/route/route_tree.cpp'
assert 'node_type == IPIN && !is_flat' in source.read_text()
sources[str(source)]=hashlib.sha256(source.read_bytes()).hexdigest();sources[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
out=root/'work/ex5p_attachment_type_profile_20261015';out.mkdir(exist_ok=False)
(out/'audit.json').write_text(json.dumps(dict(status='native_attachment_receipts_classified_by_rr_type',results=results,source_sha256=sources,scope='Actual logged branch attachment types only. IPIN/SINK restrictions in frozen VPR source depend on flat mode; counts do not prove policy illegality, causality or performance. Does not enumerate every search seed or unlogged memory access.',board_result=False,research_complete=False),indent=2)+'\n')
print(json.dumps({k:v['types'] for k,v in results.items()}))
