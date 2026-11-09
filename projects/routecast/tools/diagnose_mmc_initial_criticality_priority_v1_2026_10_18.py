"""Separate float32 criticality drift from deterministic priority reorderings."""
import json,sys,struct,ast,math
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from prediction_metrics import compare
D=R/'experiments/mmc_multiplacement_initial_criticality_v1_2026-10-18';vp=D/'independent_verification_v1.json';v=json.loads(vp.read_text());assert v['status']=='pass' and all(sha(p)==h for p,h in v['bindings'].items());bindings={**v['bindings'],**closure([Path(__file__)]),str(vp):sha(vp)}
def load(case):
 p=D/case/'initial_connection_criticalities.json';rs=json.loads(p.read_text());return {x['connection_id']:x for x in rs},{x['connection_id']:struct.unpack('<f',struct.pack('<f',float(x['criticality_float32_text'])))[0] for x in rs}
old,ov=load('old');groups=defaultdict(list)
for cid,r in old.items():groups[r['net']].append(cid)
oldmax={n:max(ov[c] for c in ids) for n,ids in groups.items()};oldorder=sorted(oldmax,key=lambda n:(-oldmax[n],n));oldrank={n:i for i,n in enumerate(oldorder)}
audit=R/'tools/verify_aes_native_demand_span_ablation_hotspots_v1.py';fn=next(x for x in ast.parse(audit.read_text()).body if isinstance(x,ast.FunctionDef) and x.name=='audit_metric');ns=dict(Counter=Counter,math=math,checked=0);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(audit),'exec'),ns);bindings[str(audit)]=sha(audit)
def inversions(permutation):
 bit=[0]*(len(permutation)+1);result=0
 for seen,value in enumerate(permutation):
  i=value+1;s=0
  while i>0:s+=bit[i];i-=i&-i
  result+=seen-s;i=value+1
  while i<len(bit):bit[i]+=1;i+=i&-i
 return result
rows=[]
for case in ['case_01','case_02','case_03']:
 new,nv=load(case);assert old.keys()==new.keys() and all((new[c]['net'],new[c]['local_sink_pin'])==(old[c]['net'],old[c]['local_sink_pin']) for c in old);changed_order=[]
 for net,ids in groups.items():
  before=sorted(ids,key=lambda c:(-ov[c],old[c]['local_sink_pin'],c));after=sorted(ids,key=lambda c:(-nv[c],new[c]['local_sink_pin'],c))
  if before!=after:changed_order.append(net)
 nm={n:max(nv[c] for c in ids) for n,ids in groups.items()};order=sorted(nm,key=lambda n:(-nm[n],n));rank={n:i for i,n in enumerate(order)};inverted=inversions([oldrank[n] for n in order]);metric={}
 for name,p,t in [('physical_query_criticality',ov,nv),('NET_maximum_criticality',oldmax,nm)]:
  k=max(1,len(t)//20);metric[name]=compare(p,t,k);ns['audit_metric'](p,t,metric[name],k)
 ip=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'staged_input_verification_v1.json';dirty=set(json.loads(ip.read_text())['affected']['affected_net_ids']);row=dict(case=case,physical_queries=115572,physical_NETs=len(groups),NETs_with_changed_full_pin_order=len(changed_order),changed_pin_order_NETs_outside_endpoint_closure=sum(n not in dirty for n in changed_order),NET_maximum_priority_positions_changed=sum(rank[n]!=oldrank[n] for n in groups),NET_maximum_priority_pair_inversions=inverted,NET_maximum_priority_inversion_fraction=inverted/(len(groups)*(len(groups)-1)//2),metrics=metric);rows.append(row);print('PRIORITY DIAG',row,flush=True)
assert ns['checked']==6 and all(sha(p)==h for p,h in bindings.items())
with (D/'priority_diagnostic_v1.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,independent_histogram_metric_vectors=6,full_pin_tie_rule='Exact decoded float32 criticality descending, local_sink_pin ascending, CID ascending; matches model full order before clean retention filtering.',NET_priority_rule='Descending maximum sink criticality then numeric NET ID; diagnostic only, not a claim about native scheduler order.',scope='Exposed initial criticality diagnostics. Full NET pin-order changes do not imply changed actual search order after retention filtering. Rank agreement does not imply equivalent objectives or explain native global rerouting. No candidate or heldout quality/gain claim.'),f,indent=2)
