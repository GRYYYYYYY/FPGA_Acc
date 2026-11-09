"""Attribute candidate union-wire excess against published original NET routes."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux32_reverse_tree_2026-10-07';cp=base/'candidate.json';v=json.loads((base/'verification.json').read_text());assert v['candidate_sha256']==sha(cp);c=json.loads(cp.read_text());ep=ROOT/'experiments/mux_budget_move_cohort_2026-10-06/w32_m2/target_endpoints.json';names=json.loads(ep.read_text())['net_names'];route=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w32/canonical/design.route';graph=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/rr_graph.xml';a=ImmutableXMLAudit(graph,c['graph_sha256']);old={name:set(n for path in paths for n,s in path) for name,paths in physical_paths(route).items()};new=defaultdict(set)
for q in c['records']:
 used=new[q['net_id']];used.add(q['source'])
 for eid in q['answer']['physical_edge_ids']:e=a.graph.edges[eid];used.update((e.source,e.sink))
wire=lambda nodes:sum(a.spans[n] for n in nodes if a.types[n] in (4,5))
rows=[];affected=set(c['affected']['affected_net_ids'])
for net,used in new.items():
 name=names[str(net)];assert name in old;before=wire(old[name]);after=wire(used)
 rows.append(dict(net_id=net,name=name,affected=net in affected,published_wirelength=before,candidate_wirelength=after,excess=after-before))
assert sum(x['candidate_wirelength'] for x in rows)==v['channel_union_wirelength']==11959
assert sum(x['published_wirelength'] for x in rows)==11883
out=ROOT/'experiments/mux32_net_wire_gap_2026-10-07';out.mkdir(exist_ok=True);rows.sort(key=lambda x:(-x['excess'],x['net_id']))
r=dict(source_sha256=sha(Path(__file__)),inputs={str(p):sha(p) for p in (cp,base/'verification.json',ep,route,graph)},rows=rows,total_excess=sum(x['excess'] for x in rows),positive_excess=sum(max(0,x['excess']) for x in rows),negative_excess=sum(min(0,x['excess']) for x in rows),unchanged_net_excess=sum(x['excess'] for x in rows if not x['affected']),scope='Development wire-only attribution using published route names and original physical spans. Not feasibility or proposed cold oracle, no native acceptance/netgain.')
(out/'diagnosis.json').write_text(json.dumps(r,indent=2)+'\n');print({k:r[k] for k in ('total_excess','positive_excess','negative_excess','unchanged_net_excess')});print(rows[:10])
