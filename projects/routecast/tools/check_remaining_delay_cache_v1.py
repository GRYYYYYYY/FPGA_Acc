"""Cache hits, eviction, graph/model changes, immutable snapshot, deadline."""
import json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from remaining_delay_cache_v1 import RemainingDelayCache
class RC:
 scale=10**9;increments=[2,3]
 def initial(self,n):return 0
f=dict(node_ids=[0,1,2],row_offsets=[0,1,2,2],dest_ranks=[1,2],edge_ids=[0,1],capacities=[1]*3);out=R/'experiments/remaining_delay_cache_contract_v1_2026-10-07';out.mkdir();graph=out/'graph.fixture';graph.write_text('unchanging fixture');cache=RemainingDelayCache(graph,sha(graph),f,RC(),out/'cache',max_entries=1);a=cache.get(2);assert [a.get(n) for n in range(3)]==[5,3,0] and cache.get(2) is a and cache.hits==1
try:a.values[0]=99
except TypeError:pass
else:raise AssertionError('mutable cache data')
f['dest_ranks'][0]=2;assert cache.fields['dest_ranks'][0]==1
cache.get(1);cache.get(2);assert cache.evictions==2 and cache.misses==3
before=dict(cache.entries)
try:cache.get(0,deadline=time.perf_counter()-1)
except TimeoutError:pass
else:raise AssertionError('expired request allowed')
assert cache.entries==before
cache.rc.scale+=1
try:cache.get(2)
except ValueError:pass
else:raise AssertionError('changed scale reused')
cache.rc.scale-=1;graph.write_text('changed graph')
try:cache.get(2)
except ValueError:pass
else:raise AssertionError('changed graph reused')
(out/'receipt.json').write_text(json.dumps(dict(hit_reuses_same_view=True,fifo_eviction_pass=True,readonly_distance_bytes_pass=True,caller_fields_cannot_modify_snapshot=True,deadline_no_publication_pass=True,model_scale_change_rejected=True,graph_content_change_rejected=True,bindings={str(Path(__file__)):sha(__file__),str(R/'tools/remaining_delay_cache_v1.py'):sha(R/'tools/remaining_delay_cache_v1.py')},scope='Software immutable snapshot/lifecycle cases, not malicious Python mutation or native epoch guarantee.'),indent=2)+'\n');print('PASS')
