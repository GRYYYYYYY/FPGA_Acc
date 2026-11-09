"""Validate independent wire/work accounting on3admitted full MMC cold routes."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from native_wire_work_independent_v1 import read_spans,audit
D=R/'experiments/native_wire_work_independent_core_v1_2026-10-18';D.mkdir();C=R/'experiments/mmc_multiplacement_cold_labels_v1_2026-10-18';bindings=closure([Path(__file__)]);rows=[];cache=Cache()
with cache.installed():
 g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());old=json.loads(Path(g['previous_endpoint']).read_text());graph=Path(old['inputs']['graph']['path']);spans=read_spans(graph,old['graph_sha256']);bindings[str(graph)]=old['graph_sha256']
 for case in ['case_01','case_02','case_03']:
  vp=C/case/'verification.json';v=json.loads(vp.read_text());assert v['all_native_physical_and_canonical_pass'] and all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(vp)]=sha(vp);W=C/case/'cold';physical=json.loads((W/'physical_audit.json').read_text());a=audit(W/'native.log',W/'output.route',physical,spans);r=v['rows'][0];assert a['wirelength']==r['wirelength'] and a['iterations']==r['iterations']
  for key in ['heap_pushes','rerouted_NET_operations','rerouted_connection_operations']:assert a[key]==r['native_work']['total_'+key]
  rows.append(dict(case=case,**{k:x for k,x in a.items() if k!='rows'}));print('PASS independent native wire/work',rows[-1],flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all3_archived_routes_wire_and_complete_iteration_counters_exact=True,scope='OriginalXML channel length and full printed NET union replay plus independent lexical iteration parse. This validates auditor against admitted cold routes only; new15arm outcomes and timing evidence remain separate.'),f,indent=2)
