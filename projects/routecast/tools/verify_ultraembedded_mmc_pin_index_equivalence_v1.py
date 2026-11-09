"""Full MMC candidate pin-index mapping and canonical byte equivalence."""
import json,re,sys,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from audit_native_route import NODE
base=R/'experiments/ultraembedded_mmc_continuous_workflow_v2_2026-10-08/seed'
source=base/'native/mmc/output.route';canonical=base/'canonical/mmc';graph=base/'rr/mmc/rr_graph.xml'
out=R/'experiments/ultraembedded_mmc_pin_index_equivalence_v1_2026-10-08';out.mkdir()
files=[source,canonical/'identity.jsonl',canonical/'design.place',canonical/'design.route',graph,Path(__file__),R/'tools/native_resume_prototype/canonical_reload_ignored_invariants_v1.py',R/'tools/native_resume_prototype/canonical_reload_pin_index_v2.py']
bindings={str(p):sha(p) for p in files}
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='All 115572 native SINK occurrences; old exact scan vs candidate multivalue index, complete canonical route bytes. No elapsed performance or native reload candidate certification.'),indent=2)+'\n')
nets={}
for line in (canonical/'identity.jsonl').read_text().splitlines():
 row=json.loads(line);assert row['name'] not in nets;nets[row['name']]=row
sites={}
for name,row in nets.items():
 index={}
 for pin in row['pins']:
  if pin['index']>0:index.setdefault(tuple(pin[k] for k in ('x','y','layer','class')),[]).append(pin)
 sites[name]=index
text=source.read_text();needed=set()
for line in text.splitlines():
 m=NODE.match(line)
 if m and m[2]=='SINK':needed.add(int(m[1]))
locations={}
for event,element in ET.iterparse(graph,events=('end',)):
 if element.tag=='node':
  nid=int(element.get('id'))
  if nid in needed:
   assert element.get('type')=='SINK' and nid not in locations
   loc=element.find('loc');locations[nid]=tuple(int(loc.get(k,'0')) for k in ('xlow','ylow','layer','ptc'))
  element.clear()
 elif element.tag in ('edge','switch','segment'):element.clear()
assert set(locations)==needed
sections={};head=[];record=None;count=0
for line in text.splitlines():
 m=re.match(r'^Net\s+(\d+)\s+\((.*?)\)',line)
 if m:
  record=nets[m[2]];nid=record['net_id'];assert nid not in sections
  sections[nid]=[re.sub(r'^Net\s+\d+',f'Net {nid}',line)];continue
 if record is None:head.append(line);continue
 m=NODE.match(line)
 if m and m[2]=='SINK':
  site=locations[int(m[1])]
  old=[pin for pin in record['pins'] if pin['index']>0 and tuple(pin[k] for k in ('x','y','layer','class'))==site]
  new=sites[record['name']].get(site,[]);assert old==new and len(new)==1
  line=re.sub(r'Net_pin_index:\s*\d+',f"Net_pin_index: {new[0]['index']}",line);count+=1
 sections[record['net_id']].append(line)
assert count==115572
head[0]='Placement_File: design.place Placement_ID: SHA256:'+sha(canonical/'design.place')
lines=head[:]
for nid in sorted(sections):lines.extend(sections[nid])
expected=('\n'.join(lines)+'\n').encode();assert expected==(canonical/'design.route').read_bytes()
assert all(sha(k)==v for k,v in bindings.items())
result=dict(bindings=bindings,all_sink_occurrences=count,all_original_scan_and_multivalue_index_pin_lists_exact=True,complete_canonical_route_byte_identical=True,scope='Full seed MMC mapping and byte equivalence, no candidate native reload or speed/stability proof.')
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(count,'full mapping and canonical bytes PASS')
