"""Independent binary32 single-node cost audit of linker-observed queries."""
import json,struct,math
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_native_query_trial_v1_2026-10-20'
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]
def value(x):return struct.unpack('<f',struct.pack('<I',x))[0]
def bits(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def main():
 source=D/'verification.json';v=json.loads(source.read_text());assert len(v['rows'])==18;rows=[];bindings={str(source):sha(source),str(__file__):sha(__file__)}
 for case in sorted(x['case'].rsplit('/',1)[0] for x in v['rows'] if x['case'].endswith('/capture')):
  row=next(x for x in v['rows'] if x['case']==case+'/capture');assert row['callback_sequence_complete'] and row['nonclock_iteration_summaries_equal'] and row['terminal_physical_sequences_equal'];p=D/case/'capture/queries.tsv';assert sha(p)==row['files'][str(p)];bindings[str(p)]=sha(p);mappingp=R/'experiments/prince_resident_consumer_v1_2026-10-20'/case/'NET_mapping.json';eligible={x['native_NET_id'] for x in json.loads(mappingp.read_text()) if not x['ignored_global']};groups=calls=assigned=unknown=nonconfig=verified=0;iterations=set();nets=set();zero_occ=0
  for line in p.open():
   iteration,encoded,node,kind,occ,cap,pres,acc,base,cost,nc,count=map(int,line.split());assert 1<=iteration<=row['iterations'] and count>0 and cap>=0;groups+=1;calls+=count;iterations.add(iteration)
   if encoded:assert encoded-1 in eligible;assigned+=count;nets.add(encoded-1)
   else:unknown+=count
   zero_occ+=count*(occ==0)
   if nc:nonconfig+=count;continue
   present=f32(1.0+f32(value(pres)*(occ+1-cap))) if occ>=cap else 1.0
   expected=f32(f32(value(base)*value(acc))*present);assert bits(expected)==cost,(case,iteration,node,expected,value(cost));verified+=count
  assert calls>0 and assigned>0 and verified>0;rows.append(dict(case=case,unique_query_state_groups=groups,cost_calls=calls,assigned_marker_calls=assigned,unassigned_marker_calls=unknown,nonconfigurable_calls_not_scalar_audited=nonconfig,independently_scalar_verified_calls=verified,zero_occupancy_calls=zero_occ,NETs_with_assigned_queries=len(nets),observed_iterations=sorted(iterations)))
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items());out=D/'query_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='LINKER_OBSERVED_QUERY_COSTS_VERIFIED',rows=rows,bindings=bindings,scope='Cross-object linker-wrapped calls only; no proof of all inlined/same-object calls. NET is instrumentation marker after setup inside fanout span, not independently verified per-connection identity or complete release ledger. Original return forwarded; nonconfigurable aggregate calls excluded from single-node scalar audit. No predictive mutation or native/fullpaid utility claim.'),indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
