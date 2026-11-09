"""Fresh cold baseline/private class-memo contexts plus actual prediction parity."""
import json,time,hashlib
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from freeze_priority_family import closure
from owner_union_wire_rc_context_cached import OwnerUnionWireRCContext as Baseline
from owner_union_wire_rc_context_cached_classes import OwnerUnionWireRCContext as Optimized
from cached_rr_endpoint_context import clear_cache as clear_original
from cached_rr_endpoint_context_classes import clear_cache as clear_private
from capacity_local_demand import CapacityAbsoluteDemand
from resident_initial_prediction_engine import predict_joint
from resident_four_repair_engine import repair_moved_history
from owned_reverse_graph import OwnedReverseGraph
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/priority_frozen_evaluation_2026-10-07';out=ROOT/'experiments/priority_class_memo_context_2026-10-07';out.mkdir();sources=closure([Path(__file__)]);binary=ROOT/'experiments/mux_owned_bound_cache_2026-10-06/search.so';sources[str(binary)]=sha(binary);inputs={str(base/f'n{n}/endpoints.json'):sha(base/f'n{n}/endpoints.json') for n in [32,64,128]};p=dict(sources=sources,inputs=inputs,scope='Development exact class-denominator memo optimization. Baseline then private cold contexts each case with separate cleared RR caches. Graph fields/scale/increments/native costs compared outside init clocks; optimized actual initial+repair prediction must equal all frozen outputs, failures included. Single observations, OS cache not reset, not fullgain/newholdout.');(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[]
def same_node(a,b):return a.tag==b.tag and dict(a.attrib)==dict(b.attrib) and len(a.children)==len(b.children) and all(same_node(x,y) for x,y in zip(a.children,b.children))
for n in [32,64,128]:
 ep=base/f'n{n}/endpoints.json';clear_original();clear_private();tick=time.perf_counter();a=Baseline(ep,weight_ns=Fraction(1,20));baseline_seconds=time.perf_counter()-tick;tick=time.perf_counter();b=Optimized(ep,weight_ns=Fraction(1,20));optimized_seconds=time.perf_counter()-tick
 assert a.context[1]==b.context[1] and a.context[5]==b.context[5];assert a.rc.scale==b.rc.scale and a.rc.increments==b.rc.increments and all(a.rc.fields[k]==b.rc.fields[k] for k in a.rc.fields);assert all(same_node(x,y) for x,y in zip(a.context[2],b.context[2]));assert len(a.context[2])==len(b.context[2]);assert all(x.tobytes()==y.tobytes() for x,y in zip(a.native.arrays,b.native.arrays));assert a.penalties==b.penalties
 b.native.__class__=CapacityAbsoluteDemand;b.native.demand_epoch=b.native.delta_calls=b.native.delta_writes=b.native.publication_calls=b.native.publication_writes=0;b.demand_journal=[];b.demand_stats=dict(calls=0,writes=0,visited=0,seconds=0.0);owned=OwnedReverseGraph(b.native.n,len(b.rc.fields['edge_ids']),b.native.ptrs[0],b.native.ptrs[1],b.native.ptrs[2],b.native.ptrs[5],binary);b.native.lib.rc_query=owned.bridge;tick=time.perf_counter()
 try:
  candidate=predict_joint(b,max_labels=10000,fallback_limit=0);candidate['history']={}
  if candidate['failure'] is not None and candidate['failure']['status']=='UNREACHABLE':candidate=repair_moved_history(b,candidate)
 finally:owned.close()
 search=time.perf_counter()-tick;file=out/f'n{n}.json';file.write_text(json.dumps(candidate,indent=2)+'\n');assert sha(file)==sha(base/f'n{n}/candidate.json');rows.append(dict(width=n,baseline_cold_context_seconds=baseline_seconds,optimized_cold_context_seconds=optimized_seconds,search_repair_seconds=search,all_graph_state_equal=True,whole_prediction_bytes_equal=True,candidate_sha256=sha(file)));print(rows[-1],flush=True);(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,complete=len(rows)==3),indent=2)+'\n')
assert all(sha(f)==d for f,d in sources.items())
