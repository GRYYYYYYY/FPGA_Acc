"""Even zero-read cache hits must reject ended owner transactions."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from criticality_dependency_reference_adapter_v2 import Graph
from compiled_criticality_tree_v1 import NativePrices
from native_price_buffer_store_v1 import Store
from cached_multiplicative_occupancy_context_v1 import Context
from fractions import Fraction
f=dict(row_offsets=[0,1,1],dest_ranks=[1],capacities=(1,1));base=(3,4);store=Store(f,base);context=Context(store,f['capacities'],base,1,{})
context.start_round({},0,{0:1});snapshot=context.begin({0});prices=NativePrices(base,snapshot);graph=Graph(f,[1],[0,0])
for _ in range(2):assert graph.tree(0).expand(0,Fraction(1,2),prices,10)['committed']
assert graph.stats['hits']==1 and graph.stats['actual_searches']==1
context.finish()
try:graph.tree(0).expand(0,Fraction(1,2),prices,10)
except RuntimeError:pass
else:raise AssertionError('stale zero-read hit accepted')
graph.close()
try:graph.tree(0)
except RuntimeError:pass
else:raise AssertionError('closed graph accepted')
store.close()
out=R/'experiments/criticality_dependency_reference_adapter_contract_v2_2026-10-15';out.mkdir();(out/'verification.json').write_text(json.dumps(dict(bindings=closure([Path(__file__)]),all_pass=True,actual_zero_read_hit_then_stale_rejection=True,closed_graph_rejection=True,scope='Explicit current serial Context validation before cache hits, including empty price read sets. Full model and independent audits remain separate.'),indent=2)+'\n');print('PASS active, zero-read hit, stale-context and closed-graph guards')
