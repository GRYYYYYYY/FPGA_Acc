"""Paid full MMC actual-native source checkpoint with cached floor scope."""
import json,time,resource
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from source_binding_v2 import closure
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18';tick=time.perf_counter()
gp=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';g=json.loads(gp.read_text());ep=Path(g['previous_endpoint']);route=Path(g['previous_native_route']);old=json.loads(ep.read_text())
fp=R/'experiments/mmc_retained_tree_full_schedule_recovery_v1_2026-10-13/model/floors.json';ap=R/'experiments/mmc_old_floor_cache_audit_v1_2026-10-18/verification.json';audit=json.loads(ap.read_text());assert not audit['new_independent_minimum_certificate_for_all_old_floors'];assert audit['bindings'][str(fp)]==sha(fp);assert all(sha(p)==h for p,h in audit['bindings'].items())
bindings={**closure([Path(__file__)]),**audit['bindings'],str(ap):sha(ap),str(gp):sha(gp),str(ep):sha(ep),str(route):sha(route)}
print('MMC NATIVE SOURCE IMPORT START',flush=True)
graph,digest,nodes,f,rc,queries=load_endpoints(ep);paths,rows,ledger=load_complete(route,old,nodes,f,rc);import_seconds=time.perf_counter()-tick
floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};byid={x['connection_id']:x for x in rows};records=[];independent=Counter();anchors=0
for q in sorted(queries,key=lambda q:q['connection_id']):
 cid=q['connection_id'];row=byid[cid];floor=floors[q['source'],q['sink']];delay=row['delay_integer'];assert floor<=delay
 proxy=max(rc.scale//10**9,(3*floor+1)//2);budget=max(proxy,delay);anchors+=delay>proxy
 records.append(dict(q,answer=dict(status='FOUND',physical_edge_ids=row['physical_edge_ids'],delay=delay),floor_integer=floor,budget_integer=budget,proxy_budget_integer=proxy));independent.update(n for n,switch in paths[cid])
frame=dict(records=records,scale=rc.scale,required_connections=len(queries),completed_connections=len(records),ledger=dict(ledger.occupancy),history={},epochs={str(net):0 for net in {q['net_id'] for q in queries}},overflow_units=0,budget_policy='NATIVE_ANCHORED_PROXY_V1',scope='Actual old native source checkpoint with cached old floors; no new per-design minimum dual certificate.',independent_connection_ledger=dict(independent))
with (D/'initial.json').open('x') as o:json.dump(frame,o);o.write('\n')
# Authenticate clean paths/metadata against already certified new warm fixture.
wroot=R/'experiments/mmc_native_feedback_inputs_v1_2026-10-18/warm';wp=wroot/'verification.json';w=json.loads(wp.read_text());assert all(sha(p)==h for p,h in w['bindings'].items());warm=json.loads((wroot/'initial.json').read_text());dirty=set(w['dirty_nets']);source={r['connection_id']:r for r in records};checks=0
for record in warm['records']:
 if record['net_id'] not in dirty:
  assert json.dumps(record)==json.dumps(source[record['connection_id']]);checks+=1
assert checks==115092 and len(records)==115572
bindings.update({str(wp):sha(wp),str(wroot/'initial.json'):sha(wroot/'initial.json'),str(D/'initial.json'):sha(D/'initial.json')})
assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,connections=len(records),nets=len(ledger.nodes),anchored_above_proxy=anchors,import_seconds=import_seconds,total_source_production_seconds=time.perf_counter()-tick,clean_warm_records_serialization_exact=checks,all_old_per_design_minima_independently_recertified=False,independent_audit_pending=True,maxrss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
with (D/'receipt.json').open('x') as o:json.dump(result,o,indent=2)
print('MMC NATIVE SOURCE COMPLETE',len(records),'clean matches',checks,'seconds',result['total_source_production_seconds'],flush=True)
