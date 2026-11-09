"""Independent15arm originalXML/NET-union wire and complete log-counter proof."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from native_wire_work_independent_v1 import read_spans,audit
D=R/'experiments/mmc_v2_native_utility_v1_2026-10-18';cp=D/'cohort_complete.json';C=json.loads(cp.read_text());assert C['all15_native_FULL_physical_and_canonical_semantic_pass'];core=R/'experiments/native_wire_work_independent_core_v1_2026-10-18/verification.json';cv=json.loads(core.read_text());assert cv['status']=='pass';bindings={**C['bindings'],**cv['bindings'],**closure([Path(__file__)]),str(cp):sha(cp),str(core):sha(core)};P=json.loads((R/'experiments/mmc_v2_native_seed_inputs_v1_2026-10-18/protocol.json').read_text());rows=[];cache=Cache()
with cache.installed():
 assert all(sha(p)==h for p,h in bindings.items());g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=json.loads(Path(g['previous_endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);spans=read_spans(graph,ep['graph_sha256'])
 for case in P['case_order']:
  vp=D/case/'verification.json';v=json.loads(vp.read_text());assert v['all_native_physical_and_canonical_pass'] and all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(vp)]=sha(vp)
  for r in v['rows']:
   W=D/case/r['arm'];physical=json.loads((W/'physical_audit.json').read_text());assert physical['inputs_sha256']['route']==sha(W/'output.route') and physical['inputs_sha256']['graph']==ep['graph_sha256'];a=audit(W/'native.log',W/'output.route',physical,spans);assert a['iterations']==r['iterations'] and a['wirelength']==r['wirelength'];assert len(a['rows'])==len(r['native_work']['rows'])
   for actual,expected in zip(a['rows'],r['native_work']['rows']):assert all(actual[k]==expected[k] for k in actual)
   for key in ['heap_pushes','rerouted_NET_operations','rerouted_connection_operations']:assert a[key]==r['native_work']['total_'+key]
   rows.append(dict(case=case,arm=r['arm'],**{k:v for k,v in a.items() if k!='rows'}));print('PASS15ARM COUNTERS',case,r['arm'],a['wirelength'],a['heap_pushes'],flush=True)
 assert len(rows)==15 and all(sha(p)==h for p,h in bindings.items())
with (D/'independent_wire_work_verification_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all15_original_XML_wire_and_log_work_counters_independently_equal=True,scope='Independent full native NET-union reconstruction/positive channel lengths and lexical every-iteration field equality, not reused producer regex. Timing/canonical/FULL admission from existing cohort proof; no fullflow performance or candidate quality promotion.'),f,indent=2)
