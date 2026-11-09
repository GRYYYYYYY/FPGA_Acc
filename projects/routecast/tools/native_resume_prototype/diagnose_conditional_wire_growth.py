"""Exact perNET RR-channel union span accounting for the native-verified replacements."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_conditional_materialized_comparison_v2_2026-10-07';vf=out/'verification.json';v=json.loads(vf.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());rows=[]
for row in v['rows']:
 w=row['width'];i=1 if w==16 else 3;graph=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/rr_graph.xml';xml=ET.parse(graph).getroot();span={}
 for n in xml.find('rr_nodes'):
  if n.get('type') not in ('CHANX','CHANY'):continue
  loc=n.find('loc');span[int(n.get('id'))]=1+int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))
 old=ROOT/f'experiments/native_resume_singlepass_floor_w{w}_m{i}_workflow_2026-10-07/canonical/design.route';new=ROOT/f'experiments/native_resume_conditional_materialized_v3_w{w}_m{i}_2026-10-07/canonical/design.route';paths=[physical_paths(f) for f in (old,new)];unions=[{name:{n for path in ps for n,_ in path if n in span} for name,ps in p.items() if ps} for p in paths];wire=[{name:sum(span[n] for n in ns) for name,ns in u.items()} for u in unions]
 assert sum(wire[0].values())==row['original_candidate_wire'] and sum(wire[1].values())==row['wirelength'];pernet=[dict(net=name,old_wire=wire[0][name],new_wire=wire[1][name],delta=wire[1][name]-wire[0][name]) for name in row['selected_net_names']]
 assert sum(x['delta'] for x in pernet)==row['candidate_wire_change']
 rows.append(dict(width=w,per_net=pernet,whole_union_wire_exact_native=True,bindings={str(f):sha(f) for f in (graph,old,new)}))
(out/'wire_diagnosis.json').write_text(json.dumps(dict(native_verification_sha256=sha(vf),rows=rows,producer_sha256=sha(Path(__file__)),scope='Every NET channel union counted once; exact original native wire parity. Shared physical route parser; no delay/wire weighted candidate search or end-to-end gain.'),indent=2)+'\n');print(rows)
