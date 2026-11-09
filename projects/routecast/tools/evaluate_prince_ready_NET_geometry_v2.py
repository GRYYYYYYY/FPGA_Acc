"""Retrospective geometry attribution using frozen same-phase boxes, no forecaster."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from verify_prince_ready_owner_forecast_v1 import ready_inverse,final_inverse
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_ready_NET_geometry_v2_2026-10-20';S=E/'prince_competitive_frontier_trial_v1_2026-10-20';H=E/'prince_cumulative_prefix_novelty_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def inside(point,box):
 x,y,z=point;return box[0]<=x<=box[1] and box[2]<=y<=box[3] and box[4]<=z<=box[5]
def main():
 frozen=load(D/'frozen_inputs.json');assert all(sha(p)==h for p,h in frozen['bindings'].items());hist={r['case']:r for r in load(H/'frozen_inputs.json')['rows']};bindings={str(p):sha(p) for p in [D/'frozen_inputs.json',H/'frozen_inputs.json',Path(__file__)]};rows=[]
 for row in frozen['rows']:
  c=row['case']
  if row['status']!='READY_GEOMETRY_FROZEN_NO_LABELS':rows.append(dict(case=c,status=row['status']));continue
  t=row['ready_iteration'];src=S/c/'capture';op=src/'owners'/f'owners_{t}.bin';lp=src/'queries.tsv.ledger.bin';ready=ready_inverse(op);final=final_inverse(lp);new={(net,n) for n,ns in final.items() for net in ns if net not in ready.get(n,set())};retained={(net,n) for n,ns in final.items() for net in ns if net in ready.get(n,set())};hpath=Path(hist[c]['path']);history={}
  for x in map(json.loads,hpath.open()):
   key=x['net'],x['node']
   if key in new:history[key]=x
  points={x['id']:x['drive_point'] for x in map(json.loads,Path(row['points']).open())};boxes={x['native_NET']:x for x in map(json.loads,Path(row['NET_boxes']).open())};groups={name:Counter() for name in ['preheap','pop']};missed={name:Counter() for name in ['preheap','pop']};folder=D/c;ap=folder/'new_owner_pair_attribution.jsonl'
  with ap.open('x') as f:
   for net,n in sorted(new):
    b=boxes[net];assert not b['ignored_global'];point=points[n];contained=inside(point,b['box']);observed=history.get((net,n),{});r=dict(net=net,node=n,inside_captured_ready_box=contained,ready_connection_active=b['ready_connection_active'],ever_preheap=bool(observed.get('preheap_events')),ever_valid_pop=bool(observed.get('pop_events')),outside_axes=[axis for axis,(x,lo,hi) in enumerate(zip(point,b['box'][::2],b['box'][1::2])) if not lo<=x<=hi]);f.write(json.dumps(r,separators=(',',':'))+'\n')
    for name,flag in [('preheap',r['ever_preheap']),('pop',r['ever_valid_pop'])]:
     key=f'observed={int(flag)},inside={int(contained)},active={int(r["ready_connection_active"])}';groups[name][key]+=1
     if not flag:missed[name]['total']+=1;missed[name]['inside']+=contained;missed[name]['outside']+=not contained;missed[name]['ready_active']+=r['ready_connection_active']
  control=Counter('inside' if inside(points[n],boxes[net]['box']) else 'outside' for net,n in retained);assert sum(control.values())==len(retained) and all(sum(g.values())==len(new) for g in groups.values());rows.append(dict(case=c,status='READY_GEOMETRY_ATTRIBUTED',new_final_owner_pairs=len(new),groups={n:dict(g) for n,g in groups.items()},unobserved={n:dict(g) for n,g in missed.items()},retained_ready_owner_control=dict(control),pair_file=str(ap)));print('READY_GEOMETRY_ATTRIBUTED',c,{name:dict(x) for name,x in missed.items()},'retained',dict(control),flush=True)
  for p in [op,lp,hpath,ap]:bindings[str(p)]=sha(p)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items())
 with (D/'verification.json').open('x') as f:json.dump(dict(status='CAPTURED_READY_BOX_GEOMETRY_ATTRIBUTION_NOT_CAUSAL_OR_PREDICTOR',rows=rows,bindings=bindings,full9_gate=False,scope='Ready pre-dynamic box containment only,not actual subsequent/per-connection highfanout/retry BB,graph reachability or proof of why native did not visit a node. No original quality/native/fullpaid/unseen/hardware admission.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
