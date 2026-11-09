"""Fixed all-case prediction entrypoint; endpoint-only input, no native labels."""
import json,time
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from owner_union_wire_rc_context_cached import OwnerUnionWireRCContext
from resident_initial_prediction_engine import predict_joint
from resident_four_repair_engine import repair_moved_history
from capacity_local_demand import CapacityAbsoluteDemand
from owned_reverse_graph import OwnedReverseGraph
ROOT=Path(__file__).resolve().parents[1]
def predict(endpoint,output):
 tick=time.perf_counter();ctx=OwnerUnionWireRCContext(endpoint,weight_ns=Fraction(1,20));ctx.native.__class__=CapacityAbsoluteDemand
 ctx.native.demand_epoch=ctx.native.delta_calls=ctx.native.delta_writes=ctx.native.publication_calls=ctx.native.publication_writes=0
 ctx.demand_journal=[];ctx.demand_stats=dict(calls=0,writes=0,visited=0,seconds=0.0)
 binary=ROOT/'experiments/mux_owned_bound_cache_2026-10-06/search.so';owned=OwnedReverseGraph(ctx.native.n,len(ctx.rc.fields['edge_ids']),ctx.native.ptrs[0],ctx.native.ptrs[1],ctx.native.ptrs[2],ctx.native.ptrs[5],binary);ctx.native.lib.rc_query=owned.bridge;setup=time.perf_counter()-tick;tick=time.perf_counter()
 try:
  c=predict_joint(ctx,max_labels=10000,fallback_limit=0);c['history']={}
  if c['failure'] is not None and c['failure']['status']=='UNREACHABLE':c=repair_moved_history(ctx,c)
 finally:owned.close()
 Path(output).write_text(json.dumps(c,indent=2)+'\n');return dict(status=c['status'],failure=c['failure'],setup_seconds=setup,search_repair_seconds=time.perf_counter()-tick,candidate_sha256=sha(output))
