"""Audit serialization against selected paths plus original VPR FULL/STA evidence."""
import json,re
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from stream_native_route_audit import audit
from immutable_xml_prediction_audit import ImmutableXMLAudit
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_d128_updated_native_import_2026-10-06';r=json.loads((out/'receipt.json').read_text());parent=root/'experiments/gf2_recurrence_placement_updates_2026-10-06/gf2_d128';selected=json.loads((parent/'receipt.json').read_text());sv=json.loads((parent/'verification.json').read_text());assert sv['receipt_sha256']==sha(parent/'receipt.json') and sv['accepted_paths_checked']==908 and r['parent_sha256']==sha(parent/'receipt.json');endpoint_dir=root/'experiments/gf2_d128_placement_swap_2026-10-06';ep=json.loads((endpoint_dir/'endpoints.json').read_text());mapping=json.loads((endpoint_dir/'mapping.json').read_text());assert r['endpoint_sha256']==sha(endpoint_dir/'endpoints.json') and r['mapping_sha256']==sha(endpoint_dir/'mapping.json');assert all(sha(p)==h for p,h in r['files_sha256'].items()) and sha(r['command'][0])==r['binary_sha256'] and sha(r['identity_command'][0])==r['identity_binary_sha256'] and r['source_sha256']==sha(root/'tools/trial_gf2_d128_updated_native_import.py');graph=Path(ep['inputs']['graph']['path']);digest=ep['graph_sha256'];work=root/'work/gf2_d128_updated_native_import_2026-10-06';physical=audit(graph,work/'design.route');assert len(physical['connections'])==908 and not physical['overflow_units'];xml=ImmutableXMLAudit(graph,digest)
import xml.etree.ElementTree as ET
node_locations={int(n.get('id')):dict(n.find('loc').attrib) for n in ET.parse(graph).getroot().find('rr_nodes')};bindings=json.loads((out/'pin_bindings.json').read_text());assert r['pin_bindings_sha256']==sha(out/'pin_bindings.json');identity={row['name']:row for row in map(json.loads,(work/'identity.jsonl').read_text().splitlines())};details=defaultdict(list)
for d in mapping['pin_details']:
 if d['role']=='SINK':details[d['net_id']].append(d)
offsets=defaultdict(int);seen_native=set()
for q in ep['connections']:
 net=q['net_id'];d=details[net][offsets[net]];offsets[net]+=1;name=ep['net_names'][str(net)];native=identity[name];options=[p for p in native['pins'] if p['index']>0 and (p['block'],p['port'],p['bit'],p['physical_pin'])==(d['block'],d['port'],d['bit'],d['physical_pin_ptc'])];assert len(options)==1;assert bindings[str(q['connection_id'])]=={'native_net_id':native['net_id'],'native_pin_index':options[0]['index'],'net_name':name,'packed_pin':d};pair=(native['net_id'],options[0]['index']);assert pair not in seen_native;seen_native.add(pair);driver=[p for p in native['pins'] if p['index']==0];assert len(driver)==1;loc=node_locations[q['source']];assert (driver[0]['x'],driver[0]['y'],driver[0]['layer'],driver[0]['class'])==(int(loc['xlow']),int(loc['ylow']),int(loc.get('layer','0')),int(loc['ptc']))
edge_lookup=defaultdict(list)
for eid in range(len(xml.graph.edges)):
 e=xml.graph.edges[eid];edge_lookup[e.source,e.sink,e.switch_id].append(eid)
expected={(bindings[str(q['connection_id'])]['native_net_id'],bindings[str(q['connection_id'])]['native_pin_index']):q['answer']['physical_edge_ids'] for q in selected['records']};actual={};net=None;prefix={};current=[];previous=None;switch=None
work=root/'work/gf2_d128_updated_native_import_2026-10-06'
for line in (work/'design.route').read_text().splitlines():
 m=re.match(r'^\s*Net\s+(\d+)\s+\(',line)
 if m:net=int(m[1]);prefix={};current=[];previous=None;switch=None;continue
 m=re.match(r'^Node:\s*(\d+).*?Switch:\s*(-?\d+)(?:\s+Net_pin_index:\s*(\d+))?',line)
 if not m:continue
 node=int(m[1])
 if node in prefix:current=prefix[node].copy()
 elif previous is not None and switch is not None and switch>=0:
  candidates=edge_lookup[previous,node,switch];assert len(candidates)==1;current=current+[candidates[0]];prefix[node]=current.copy()
 else:current=[];prefix[node]=[]
 previous=node;switch=int(m[2])
 if m[3] is not None:key=(net,int(m[3]));assert key not in actual;actual[key]=current.copy()
assert actual==expected
log=(work/'import.log').read_text();assert r['exit_code']==0 and r['native_success'] and 'RouterOpts.check_route: FULL' in log and 'Completed routing consistency check successfully.' in log and 'VPR succeeded' in log;cpd=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1]);assert cpd==r['cpd_ns'];mismatches=int(re.search(r'Found (\d+) mismatches',log)[1]);fixups=int(re.search(r'Fixed (\d+) routing traces',log)[1]);baseline=root/'experiments/gf2_d128_swapped_place_cold_2026-10-06';br=json.loads((baseline/'receipt.json').read_text());baseline_work=Path(json.loads((baseline/'protocol.json').read_text())['cwd']);assert all(sha(work/n)==sha(baseline_work/n) for n in ('design.blif','design.net'));assert [line.split() for line in (work/'design.place').read_text().splitlines()]==[line.split() for line in (baseline_work/'design.place').read_text().splitlines()]
(out/'verification.json').write_text(json.dumps({'complete_selected_connections':908,'serialized_paths_exactly_match_selection':True,'overflow_units':0,'native_FULL_success':True,'cpd_ns':cpd,'reference_cpd_ns':br['cpd_ns'],'packing_mismatches':mismatches,'packing_trace_fixups':fixups,'receipt_sha256':sha(out/'receipt.json'),'scope':'Independently packedpin-mapped complete tseng predicted nonzeroRC complete physical paths/nativeFULL and STA success, no original reference path copying; raw input serialization exactly preserved selected paths. Native sync has fixups; canonical zero-fixup/post-sync physical preservation not yet proved. New same-architecture tseng case only, not independently certified family holdout; no representative end-to-end speed or production publication proof.'},indent=2)+'\n');print('verified908 selected serialized paths, zerooverflow, nativeFULL/STA',cpd,'fixups',fixups)
