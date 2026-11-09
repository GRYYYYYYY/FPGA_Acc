"""Audit prospective source closure and actual loaded modules for indexed pipeline."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(Path(__file__).resolve().parent),str(R/'tools/native_route_transaction')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from indexed_integer_rc import IndexedIntegerRC
from live_mailbox_thread_v6 import Worker
seq=R/'experiments/native_resume_postroute_batch_integrated_adder_2026-10-07';p=json.loads((seq/'protocol.json').read_text());required=[R/'tools/native_resume_prototype'/name for name in ('indexed_integer_rc.py','shared_inventory_exchange_local.py','current_global_budget_batch.py','serialize_shared_inventory.py','source_binding_v2.py')]+[R/'tools/native_route_transaction'/name for name in ('live_mailbox_thread_v6.py','live_search_worker_v11.py','live_endpoint_binding_v3.py','live_search_client_v3.py')]
assert all(p['sources'][str(f)]==sha(f) for f in required);assert all(sha(f)==h for f,h in p['sources'].items())
actual=[]
for name,module in list(sys.modules.items()):
 file=getattr(module,'__file__',None)
 if file is None:continue
 path=Path(file).resolve()
 if path.suffix=='.py' and path.is_relative_to(R/'tools') and path!=Path(__file__).resolve():
  assert str(path) in p['sources'],(name,str(path));actual.append(str(path))
old=R/'experiments/native_resume_postroute_v5_integrated_adder_2026-10-07/protocol.json';op=json.loads(old.read_text());old_missing=[str(f) for f in (R/'tools/native_route_transaction/live_mailbox_thread_v2.py',R/'tools/native_route_transaction/live_search_worker_v7.py') if str(f) not in op['sources']]
(seq/'provenance_verification.json').write_text(json.dumps(dict(protocol_sha256=sha(seq/'protocol.json'),prospectively_frozen_source_count=len(p['sources']),required_cross_directory_sources=[str(f) for f in required],actual_local_imports_in_verifier_all_frozen=actual,prior_protocol_missing_worker_sources=old_missing,verifier_sha256=sha(__file__),scope='Current top-level protocol freezes cross-directory worker/adapter/search dependencies before runs; actual imports of shared worker/adapter in this checker covered. This is not proof of arbitrary dynamic import completeness. Earlier top-level closure omitted worker sources; earlier artifact hashes/tests are not retroactively strengthened.'),indent=2)+'\n');print('PASS',len(p['sources']),len(actual))
