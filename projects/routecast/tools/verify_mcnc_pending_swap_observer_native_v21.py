"""Independent route unions, XML bins, tie ranks, and canonical path parity."""
import json,sys,math,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from native_route_ledger_import_compact import physical_paths
out=R/'experiments/mcnc_pending_swap_observer_native_validation_v21_2026-10-07';parent=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(path)==h for path,h in bindings.items());(out/'verification_protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Post-outcome independent XML-bin vectors and tied-rank metric calculation, native-path/ledger/full-quality/cost boundaries. Single development case, no heldout performance evidence.'))+'\n');rows=[]
def metrics(p,t,k):
 keys=sorted(p);assert set(keys)==set(t);k=min(k,len(keys));a=[p[x] for x in keys];b=[t[x] for x in keys]
 def rank(values):
  count=Counter(values);seen=0;result={}
  for value,n in sorted(count.items()):result[value]=seen+(n-1)/2;seen+=n
  return [result[v] for v in values]
 ar,br=rank(a),rank(b);mean=(len(a)-1)/2;cross=sum((x-mean)*(y-mean) for x,y in zip(ar,br));denom=math.sqrt(sum((x-mean)**2 for x in ar)*sum((y-mean)**2 for y in br));ps=set(sorted(keys,key=lambda x:(-p[x],x))[:k]);ts=set(sorted(keys,key=lambda x:(-t[x],x))[:k]);return dict(spearman=cross/denom if denom else None,precision_at_k=len(ps&ts)/k,recall_at_k=len(ps&ts)/k,mae=sum(abs(x-y) for x,y in zip(a,b))/len(a),universe_size=len(a),k=k)
for row in r['rows']:
 name=row['name']
 if row['native_status']=='INCOMPLETE_NOT_SUBMITTED':assert row['completed']<row['required'] and row['metrics'] is None;rows.append(dict(name=name,incomplete_retained=True));continue
 assert all(sha(path)==h for path,h in row['files'].items());bindings.update(row['files']);c=json.loads((parent/name/'candidate.json').read_text());w=out/name;norm=lambda paths:{name:Counter(paths) for name,paths in paths.items() if paths};cp=physical_paths(w/'candidate/output.route');assert norm(cp)==norm(physical_paths(w/'canonical/design.route'));cold=physical_paths(w/'cold/output.route');assert norm(cold)==norm(physical_paths(w/'cold_canonical/design.route'))
 def unions(paths):return {net:{n for path in ps for n,_ in path} for net,ps in paths.items() if ps}
 pu,tu=unions(cp),unions(cold);po=Counter(n for ns in pu.values() for n in ns);to=Counter(n for ns in tu.values() for n in ns);assert dict(po)=={int(n):v for n,v in c['ledger'].items()};ep=json.loads((R/f'experiments/mcnc_prospective_v1_2026-10-07/{name}/endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path']);caps={};spans={};channel={};bins=defaultdict(lambda:[0,0,0]);stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  par=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and par=='rr_nodes':
   n=int(e.get('id'));cap=int(e.get('capacity'));caps[n]=cap;kind=e.get('type');loc=e.find('loc')
   if kind in ('CHANX','CHANY'):
    x0,x1,y0,y1=[int(loc.get(k)) for k in ('xlow','xhigh','ylow','yhigh')];spans[n]=1+x1-x0+y1-y0
    if cap>0:
     channel[n]=(cap,po.get(n,0),to.get(n,0));seg=e.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1
     for x in range(x0,x1+1):
      for y in range(y0,y1+1):
       key=(int(loc.get('layer','0')),x,y,kind,sid);bins[key][0]+=cap;bins[key][1]+=po.get(n,0);bins[key][2]+=to.get(n,0)
  if (e.tag,par) in {('node','rr_nodes'),('edge','rr_edges')}:stack[-2].remove(e);e.clear()
  stack.pop()
 assert all(v<=caps[n] for n,v in po.items());pw=sum(sum(spans.get(n,0) for n in ns) for ns in pu.values());tw=sum(sum(spans.get(n,0) for n in ns) for ns in tu.values());assert pw==row['candidate_wirelength'] and tw==row['cold_wirelength']
 concrete=metrics({n:x[1]/x[0] for n,x in channel.items()},{n:x[2]/x[0] for n,x in channel.items()},max(1,len(channel)//20));spatial=metrics({k:x[1]/x[0] for k,x in bins.items()},{k:x[2]/x[0] for k,x in bins.items()},20)
 for kind,got in [('spatial',spatial),('concrete',concrete)]:
  for key,value in got.items():expected=row['metrics'][kind][key];assert value==expected if not isinstance(value,float) else math.isclose(value,expected,rel_tol=1e-12,abs_tol=1e-12),(kind,key,value,expected)
 for canonical in (row['candidate_canonical'],row['cold_canonical']):assert canonical['exit_code']==0 and canonical['mismatches']==canonical['fixups']==0
 assert row['workflow_complete_seconds']==row['producer_total_seconds']+row['workflow_native_validation_seconds'];quality=row['candidate_cpd_ns']<=row['cold_cpd_ns'] and pw<=tw;assert quality==row['quality_pass'];assert row['complete_gain_pass']==(quality and row['workflow_complete_seconds']<row['cold_routing_and_canonical_seconds']);rows.append(dict(name=name,all_native_and_canonical_paths_equal=True,exact_native_owner_ledger_and_wire_pass=True,independent_spatial=spatial,independent_concrete=concrete,joint_quality_pass=quality,complete_gain_pass=row['complete_gain_pass']));print('PASS',name,spatial,flush=True)
assert all(sha(path)==h for path,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(rows=rows,bindings=bindings),indent=2)+'\n')
