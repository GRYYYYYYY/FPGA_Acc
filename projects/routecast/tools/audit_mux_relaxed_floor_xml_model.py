"""Bind every relaxed-search arc/capacity to original XML electrical values."""
import json,sys
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
ROOT=Path(__file__).resolve().parents[1];w=int(sys.argv[1]);p=json.loads((ROOT/'experiments/mux_heuristic_budget_cohort_2026-10-07/protocol.json').read_text());case=next(c for c in p['cases'] if c['width']==w);ctx=PersistentRCContext(case['target']);graph=ctx.endpoint_metadata['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ctx.endpoint_metadata['graph_sha256']);ids,classes,switches,digest=read(graph);fields=ctx.rc.fields;assert len(ids)==len(fields['capacities']);count=0
for u in range(len(ids)):
 assert fields['capacities'][u]==xml.caps[u]
 for s in range(fields['row_offsets'][u],fields['row_offsets'][u+1]):
  eid=fields['edge_ids'][s];e=xml.graph.edges[eid];v=fields['dest_ranks'][s];assert (e.source,e.sink)==(u,v);assert F(ctx.rc.increments[s],ctx.rc.scale)==arc_delay(classes,switches,ids[v],e.switch_id);count+=1
assert count==len(xml.graph.edges)
source_checks=0;endpoint_bindings={}
for case in p['cases']:
 if case['width']!=w:continue
 ep=json.loads(Path(case['target']).read_text());assert ep['graph_sha256']==digest
 for q in ep['connections']:
  resistance,capacitance=classes[ids[q['source']]];assert resistance*capacitance/2==0;source_checks+=1
 endpoint_bindings[case['target']]=sha(case['target'])
out=ROOT/'experiments/mux_relaxed_floor_xml_model_2026-10-07';out.mkdir(exist_ok=True);(out/f'w{w}_verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),graph_path=graph,graph_sha256=digest,endpoint_bindings=endpoint_bindings,scale=ctx.rc.scale,nodes=len(ids),arcs=count,source_initial_zero_checks=source_checks,scope='Every CSR arc exact increment and positive-capacity domain checked against original XML node/switch Fraction values; every frozen move SOURCE initial RC term zero. Additive buffered RC model only, not native propagated load/STA or capacity realization.'),indent=2)+'\n');print(w,'XML model verified',count,'arcs',source_checks,'source checks',flush=True)
