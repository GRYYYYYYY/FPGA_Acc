"""Independent Expat drive points, binary NET boxes and printed-route attribution."""
import json,struct
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from verify_prince_BB_conditional_demand_v1 import graph as read_points
from verify_prince_ownership_ledger_v2 import owner_payload
from evaluate_prince_ready_owner_forecast_v1 import final_owners
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_ready_NET_geometry_v2_2026-10-20';S=E/'prince_competitive_frontier_trial_v1_2026-10-20';H=E/'prince_cumulative_prefix_novelty_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def main():
 frozen=load(D/'frozen_inputs.json');v=load(D/'verification.json');assert all(sha(p)==h for p,h in frozen['bindings'].items());assert all(sha(p)==h for p,h in v['bindings'].items());hist={r['case']:r for r in load(H/'frozen_inputs.json')['rows']};result={r['case']:r for r in v['rows']};graphs={};records=retained_checks=boxchecks=0;rows=[];bindings={str(p):sha(p) for p in [D/'frozen_inputs.json',D/'verification.json',Path(__file__),R/'tools/verify_prince_BB_conditional_demand_v1.py']}
 for row in frozen['rows']:
  if row['status']!='READY_GEOMETRY_FROZEN_NO_LABELS':continue
  c=row['case'];w=c.split('/')[0];t=row['ready_iteration'];src=S/c/'capture'
  if w not in graphs:
   p=E/'prince_native_cohort_v1_2026-10-20'/w/'source/rr_graph.xml';graphs[w]=read_points(p);bindings[str(p)]=sha(p)
  points=graphs[w];saved={x['id']:tuple(x['drive_point']) for x in map(json.loads,Path(row['points']).open())};assert saved==points;raw=(src/'boundary'/f'boxes_{t}.bin').read_bytes();assert raw[:8]==b'RCBOX001' and struct.unpack_from('<Q',raw,8)[0]==t;boxes={net:b for net,*b in struct.iter_unpack('<Q6i',raw[24:])};active={int(x[2]) for x in (line.split() for line in (src/'queries.tsv.connections.tsv').open()) if int(x[0])==t};fboxes={x['native_NET']:x for x in map(json.loads,Path(row['NET_boxes']).open())};mapping=load(E/'prince_resident_consumer_v1_2026-10-20'/c/'NET_mapping.json')
  assert set(boxes)==set(fboxes)
  for x in mapping:
   net=x['native_NET_id'];a=fboxes[net];assert a==dict(native_NET=net,endpoint_NET=x['endpoint_NET_id'],name=x['name'],ignored_global=x['ignored_global'],box=boxes[net],ready_connection_active=net in active);boxchecks+=1
  it,ready=owner_payload(src/'owners'/f'owners_{t}.bin');assert it==t;final=final_owners(src/'output.route');rp={(net,n) for net,ns in ready.items() for n in ns};fp={(net,n) for net,ns in final.items() for n in ns};new=fp-rp;retained=fp&rp;history={}
  for x in map(json.loads,Path(hist[c]['path']).open()):
   if (x['net'],x['node']) in new:history[x['net'],x['node']]=x
  pairrecords=list(map(json.loads,Path(result[c]['pair_file']).open()));assert len(pairrecords)==len(new) and {(x['net'],x['node']) for x in pairrecords}==new;groups={name:Counter() for name in ['preheap','pop']};unobserved={name:Counter() for name in ['preheap','pop']}
  def violations(net,n):return [axis for axis in range(3) if points[n][axis]<boxes[net][2*axis] or points[n][axis]>boxes[net][2*axis+1]]
  for x in pairrecords:
   net,n=x['net'],x['node'];outside=violations(net,n);inside=not outside;h=history.get((net,n),{});assert x==dict(net=net,node=n,inside_captured_ready_box=inside,ready_connection_active=net in active,ever_preheap=bool(h.get('preheap_phase_mask')),ever_valid_pop=bool(h.get('pop_phase_mask')),outside_axes=outside);records+=1
   for name,flag in [('preheap',x['ever_preheap']),('pop',x['ever_valid_pop'])]:
    groups[name][f'observed={int(flag)},inside={int(inside)},active={int(net in active)}']+=1
    if not flag:unobserved[name]['total']+=1;unobserved[name]['inside']+=inside;unobserved[name]['outside']+=not inside;unobserved[name]['ready_active']+=net in active
  controls=Counter('outside' if violations(net,n) else 'inside' for net,n in retained);retained_checks+=len(retained);assert dict(controls)==result[c]['retained_ready_owner_control'];assert {k:dict(x) for k,x in groups.items()}==result[c]['groups'];assert {k:dict(x) for k,x in unobserved.items()}==result[c]['unobserved'];rows.append(dict(case=c,new_owner_pairs=len(new),retained_controls=len(retained)));print('INDEPENDENT_READY_GEOMETRY_PASS',c,len(new),len(retained),flush=True)
 assert len(rows)==6 and records==8119
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL_GRAPH_POINTS_NET_BOXES_AND_OWNER_PAIR_GEOMETRY_RECONCILED',graph_resources=sum(len(x) for x in graphs.values()),NET_box_rows=boxchecks,new_owner_pairs=records,retained_owner_controls=retained_checks,rows=rows,bindings=bindings,scope='Expat graph coordinates versus primary ElementTree;native binary boxes/actual ready connections;printed final routes versus primary terminal event ledger. Geometry attribution only,not actual next-search BB or causality.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
