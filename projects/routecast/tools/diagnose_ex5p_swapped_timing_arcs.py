"""Report-level shared timing-arc diagnosis; rounded STA data, not RR mapping."""
import json,re
from decimal import Decimal
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_swapped_timing_arcs_2026-10-06';out.mkdir();sources={name:root/'work'/directory/'0/reload/report_timing.setup.rpt' for name,directory in [('predicted','ex5p_swapped_canonical_reload_2026-10-06'),('reference','ex5p_swapped_reference_canonical_reload_2026-10-06')]}
(out/'protocol.json').write_text(json.dumps({'inputs_sha256':{name:sha(p) for name,p in sources.items()},'policy':'Parse all reported data paths before arrival marker, identify directed logical point pairs; compare only identical point pairs. 0.001ns printed precision, no full-netlist coverage, no RR binding or reference-route transfer.','scope':'Development timing diagnosis after outcomes; not prediction/holdout evidence.'},indent=2)+'\n')
def parse(path):
 text=path.read_text();assert '# Unit scale: 1e-09 seconds' in text and '# Output precision: 3' in text;arcs={};paths=[]
 for section in re.split(r'^#Path \d+\s*$',text,flags=re.M)[1:]:
  start=re.search(r'^Startpoint:\s*(.*?)$',section,re.M)[1];end=re.search(r'^Endpoint\s*:\s*(.*?)$',section,re.M)[1];body=section.split('data arrival time',1)[0];points=[]
  for line in body.splitlines():
   m=re.match(r'^(.+?)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',line)
   if not m:continue
   label=m[1].strip()
   if not re.search(r'\(\.(?:input|output|names)\)$',label):continue
   points.append({'point':label,'increment_ns':m[2],'cumulative_ns':m[3]})
  assert points
  steps=[]
  for previous,current in zip(points,points[1:]):
   key=(previous['point'],current['point']);delay=Decimal(current['increment_ns']);arcs.setdefault(key,set()).add(delay);steps.append({'from':key[0],'to':key[1],'delay_ns':str(delay)})
  arrival=Decimal(re.search(r'data arrival time\s+(-?\d+\.\d+)',section)[1]);assert abs(sum((Decimal(p['increment_ns']) for p in points),Decimal(0))-arrival)<=Decimal('0.0005')*len(points)
  paths.append({'startpoint':start,'endpoint':end,'arrival_ns':str(arrival),'steps':steps})
 assert all(len(v)==1 for v in arcs.values()),'same directed arc has context-dependent delays'
 return {k:next(iter(v)) for k,v in arcs.items()},paths
p,pp=parse(sources['predicted']);r,rp=parse(sources['reference']);common=p.keys()&r.keys();deltas=[{'from':u,'to':v,'predicted_ns':str(p[u,v]),'reference_ns':str(r[u,v]),'delta_ns':str(p[u,v]-r[u,v])} for u,v in common];deltas.sort(key=lambda x:(-Decimal(x['delta_ns']),x['from'],x['to']));endpoints={x['endpoint']:x for x in rp};assert len(endpoints)==len(rp);paired=[]
for path in pp:
 if path['endpoint'] in endpoints:
  ref=endpoints[path['endpoint']];paired.append({'endpoint':path['endpoint'],'predicted_startpoint':path['startpoint'],'reference_startpoint':ref['startpoint'],'predicted_arrival_ns':path['arrival_ns'],'reference_arrival_ns':ref['arrival_ns'],'delta_ns':str(Decimal(path['arrival_ns'])-Decimal(ref['arrival_ns']))})
paired.sort(key=lambda x:-Decimal(x['delta_ns']));result={'inputs_sha256':{n:sha(p) for n,p in sources.items()},'reported_paths':{'predicted':len(pp),'reference':len(rp)},'shared_directed_arcs':len(common),'largest_shared_arc_regressions':deltas[:20],'endpoint_worst_path_comparison':paired,'predicted_worst_path':pp[0],'reference_worst_path':rp[0],'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__)),'scope':'Rounded reported-path diagnosis. Endpoint comparisons may have different startpoints/logical paths. Shared arcs identify timing differences, not complete RC causes or physical resource bindings.'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('shared arcs',len(common),'worst shared regressions',deltas[:3]);print('worst endpoint regressions',paired[:3])
