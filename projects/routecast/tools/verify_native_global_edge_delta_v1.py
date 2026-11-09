"""Full body recovery after only borrowed getter/signature/preflight substitutions."""
import json,ast
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_global_edge_source_contract_v1_2026-10-10';A=R/'build/native_live_seed_profile_v1_2026-10-10/source';B=R/'build/native_live_seed_global_edge_v1_2026-10-10/source';changes=json.loads((D/'changes.json').read_text());files=[Path(__file__),D/'changes.json']
for name,operations in changes.items():
 s=(B/name).read_text()
 for old,new in reversed(operations):
  if not new:
   needle='U v=size_t(graph.edge_sink_node(RRNodeId(u),local))';assert s.count(needle)==1;s=s.replace(needle,old+needle)
  else:assert new in s;s=s.replace(new,old)
 assert s==(A/name).read_text(),name;files.extend([A/name,B/name])
a=(R/'tools/run_native_live_seed_profile_model_v1.py').read_text();b=(R/'tools/run_native_live_seed_global_edge_model_v1.py').read_text().replace('native_live_seed_global_edge_adapter_v1','native_live_seed_profile_adapter_v1');assert ast.dump(ast.parse(a))==ast.dump(ast.parse(b));files.extend([R/'tools/run_native_live_seed_profile_model_v1.py',R/'tools/run_native_live_seed_global_edge_model_v1.py'])
(D/'verification.json').write_text(json.dumps(dict(full_search_routing_and_reverse_index_bodies_equal_after_only_getter_signature_preflight_changes=True,full_model_AST_equal_except_Search_import=True,bindings={str(p):sha(p) for p in files},scope='Const reference from public RRGraphBuilder.rr_nodes(), global edge storage getters only. Complete current row/capacity/src/dest/switch native preflight required; no private storage access, copied edge arrays or changed heap/tie/NET admission.'),indent=2)+'\n');print('GLOBAL EDGE DELTA PASS')
