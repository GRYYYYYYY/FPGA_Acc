"""All guard representations/cases, complete channel and spatial truth-cutoff ties."""
import json,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_overflow_guard_v1_2026-10-10';p=D/'comparison.json';v=json.loads(p.read_text());assert v['independent_histogram_metric_checks']==18 and all(sha(q)==h for q,h in v['bindings'].items());bindings={str(p):sha(p),str(Path(__file__)):sha(Path(__file__))};rows=[];protocol=json.loads((D/'protocol.json').read_text())
for case,root in [('original','sha1_frozen_hotspots_v2_2026-10-10'),('second_swap','sha_second_swap_hotspots_v1_2026-10-10')]:
 vp=R/'experiments'/root/'sha1/comparison_vectors.json';assert sha(vp)==v['bindings'][str(vp)];vectors=json.loads(vp.read_text());channels=vectors['channels'];bins=vectors['bins'];epfile=Path(dict(protocol['cases'])[case]);ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];incidence={};stack=[]
 for event,x in E.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(x);continue
  if x.tag=='node' and x.get('type') in ['CHANX','CHANY'] and int(x.get('capacity'))>0:
   n=int(x.get('id'));loc=x.find('loc').attrib;seg=x.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1;incidence[n]=[(int(loc.get('layer','0')),xx,yy,x.get('type'),sid) for xx in range(int(loc['xlow']),int(loc['xhigh'])+1) for yy in range(int(loc['ylow']),int(loc['yhigh'])+1)]
  if x.tag in ['node','edge']:
   if len(stack)>1:stack[-2].remove(x)
   x.clear()
  stack.pop()
 assert set(incidence)=={x['node'] for x in channels};metricrow=next(r for r in v['rows'] if r['case']==case)
 for method,filename,field in [('initial','initial.json','ledger'),('round0','round0.json','ledger'),('final_shared','sketch.json','ledger'),('final_independent','sketch.json','independent_connection_ledger')]:
  q=D/case/'model'/filename;assert sha(q)==v['bindings'][str(q)];ledger=json.loads(q.read_text())[field];spred=Counter()
  for n,keys in incidence.items():
   for k in keys:spred[k]+=ledger.get(str(n),0)
  for domain,values in [('concrete',channels),('spatial',bins)]:
   ids=[x['node'] if domain=='concrete' else tuple(x['key']) for x in values];truth={n:x['native']/x['capacity'] for n,x in zip(ids,values)};pred={n:(ledger.get(str(n),0) if domain=='concrete' else spred[n])/x['capacity'] for n,x in zip(ids,values)};m=metricrow['metrics'][method][domain];k=m['k'];boundary=m['truth_k_boundary'];strict={n for n in ids if truth[n]>boundary};ties={n for n in ids if truth[n]==boundary};selected=set(sorted(ids,key=lambda n:(-pred[n],n))[:k]);need=k-len(strict);assert 0<need<=len(ties);fixed=len(selected&strict);possible=len(selected&ties);lo=(fixed+max(0,need-(len(ties)-possible)))/k;hi=(fixed+min(need,possible))/k;assert lo<=m['precision_at_k']<=hi
   assert len(selected&set(sorted(ids,key=lambda n:(-truth[n],n))[:k]))/k==m['precision_at_k'];rows.append(dict(case=case,method=method,domain=domain,reported_precision=m['precision_at_k'],truth_tie_precision_lower=lo,truth_tie_precision_upper=hi,truth_cutoff_ties=len(ties),scope='Fixed predicted ID order, all admissible truth cutoff tie subsets.'))
assert len(rows)==16 and all(sha(q)==h for q,h in bindings.items());(D/'truth_tie_sensitivity.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n');print('ALL16 GUARD TRUTH TIE INTERVALS PASS')
