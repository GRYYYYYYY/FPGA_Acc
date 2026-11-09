"""Audit serialization against selected paths plus original VPR FULL/STA evidence."""
import json,re
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
from stream_native_route_audit import audit
from immutable_xml_prediction_audit import ImmutableXMLAudit
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_selected_native_import_2026-10-06';r=json.loads((out/'receipt.json').read_text());selection_dir=root/'experiments/nonzero_rc_lcv_selection_2026-10-06';s=json.loads((selection_dir/'receipt.json').read_text());sv=json.loads((selection_dir/'verification.json').read_text());assert sv['receipt_sha256']==sha(selection_dir/'receipt.json') and sv['complete_selection_verified'] and r['selection_sha256']==sha(selection_dir/'receipt.json');pool=json.loads((root/'experiments/nonzero_rc_pair_avoidance_2026-10-06/receipt.json').read_text());assert s['parent_sha256']==sha(root/'experiments/nonzero_rc_pair_avoidance_2026-10-06/receipt.json');assert all(sha(p)==h for p,h in r['files_sha256'].items()) and sha(r['command'][0])==r['binary_sha256'] and r['source_sha256']==sha(root/'tools/trial_nonzero_rc_selected_native_import.py');graph,digest,_,_,_,_,_=load(root);physical=audit(graph,root/'work/nonzero_rc_selected_native_import_2026-10-06/design.route');assert len(physical['connections'])==69 and not physical['overflow_units'];xml=ImmutableXMLAudit(graph,digest);edge_lookup=defaultdict(list)
for eid in range(len(xml.graph.edges)):
 e=xml.graph.edges[eid];edge_lookup[e.source,e.sink,e.switch_id].append(eid)
expected={tuple(g['key']):g['paths'][a]['answer']['physical_edge_ids'] for g,a in zip(pool['candidates'],s['selected'])};actual={};net=None;prefix={};current=[];previous=None;switch=None
work=root/'work/nonzero_rc_selected_native_import_2026-10-06'
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
log=(work/'import.log').read_text();assert r['exit_code']==0 and r['native_success'] and 'RouterOpts.check_route: FULL' in log and 'Completed routing consistency check successfully.' in log and 'VPR succeeded' in log;cpd=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1]);assert cpd==r['cpd_ns'];mismatches=int(re.search(r'Found (\d+) mismatches',log)[1]);fixups=int(re.search(r'Fixed (\d+) routing traces',log)[1]);baseline=root/'experiments/nonzero_rc_fanout_observable64_2026-10-06';br=json.loads((baseline/'receipt.json').read_text());baseline_work=Path(json.loads((baseline/'protocol.json').read_text())['cwd']);assert all(sha(work/n)==sha(baseline_work/n) for n in ('design.blif','design.net','design.place'))
(out/'verification.json').write_text(json.dumps({'complete_selected_connections':69,'serialized_paths_exactly_match_selection':True,'overflow_units':0,'native_FULL_success':True,'cpd_ns':cpd,'reference_cpd_ns':br['cpd_ns'],'packing_mismatches':mismatches,'packing_trace_fixups':fixups,'receipt_sha256':sha(out/'receipt.json'),'scope':'Independently selected nonzeroRC complete physical paths/nativeFULL and STA success, no original reference path copying; raw input serialization exactly preserved selected paths. Native sync has fixups; canonical zero-fixup/post-sync physical preservation not yet proved. Synthetic case only; no representative end-to-end speed or production publication proof.'},indent=2)+'\n');print('verified69 selected serialized paths, zerooverflow, nativeFULL/STA',cpd,'fixups',fixups)
