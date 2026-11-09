"""Exact NET-union wire differences plus native critical-path endpoint churn."""
import json,re,sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2]
ep=ROOT/'experiments/native_resume_precritical_cohort_2026-10-07/verification.json';e=json.loads(ep.read_text());assert all(sha(p)==h for p,h in e['bindings'].items())
bindings={str(ep):sha(ep),str(Path(__file__)):sha(Path(__file__)),str(ROOT/'tools/native_route_ledger_import_compact.py'):sha(ROOT/'tools/native_route_ledger_import_compact.py')};contexts={};rows=[]
for case in e['rows']:
 w,i=case['width'],case['index'];assert case['complete']
 if case['joint_nonregression']:continue
 workflow=ROOT/f'experiments/native_resume_cohort_w{w}_m{i}_workflow_2026-10-07';cold=ROOT/f'experiments/native_resume_cohort_w{w}_m{i}_cold_2026-10-07'
 oldfile=ROOT/f'experiments/mux_live_placement_updates_2026-10-06/w{w}/original_endpoints.json';newfile=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json'
 old,new=[json.loads(f.read_text()) for f in (oldfile,newfile)]
 for f in (oldfile,newfile):assert sha(f)==e['bindings'][str(f)];bindings[str(f)]=sha(f)
 original={q['connection_id']:q for q in old['connections']};dirty={new['net_names'][str(q['net_id'])] for q in new['connections'] if (q['source'],q['sink'])!=(original[q['connection_id']]['source'],original[q['connection_id']]['sink'])}
 if w not in contexts:
  graph=Path(new['inputs']['graph']['path']);assert sha(graph)==e['bindings'][str(graph)];bindings[str(graph)]=sha(graph)
  spans={}
  for _,node in ET.iterparse(graph,events=('end',)):
   if node.tag!='node':continue
   if node.get('type') in ('CHANX','CHANY'):
    loc=node.find('loc');spans[int(node.get('id'))]=1+int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))
   node.clear()
  oldroute=graph.parent/'design.route';assert sha(oldroute)==e['bindings'][str(oldroute)];bindings[str(oldroute)]=sha(oldroute)
  contexts[w]=spans,physical_paths(oldroute)
 spans,seed=contexts[w]
 routefiles=[workflow/'canonical/design.route',cold/'canonical/design.route'];routes=[physical_paths(f) for f in routefiles]
 for f in routefiles:assert sha(f)==e['bindings'][str(f)];bindings[str(f)]=sha(f)
 assert routes[0].keys()==routes[1].keys()==seed.keys()
 netrows=[]
 for name in sorted(seed):
  wire=[]
  for paths in routes:
   union={node for branch in paths[name] for node,_ in branch};wire.append(sum(spans.get(node,0) for node in union))
  retained=Counter(routes[0][name])==Counter(seed[name])
  netrows.append(dict(name=name,wire_resume=wire[0],wire_cold=wire[1],wire_delta=wire[0]-wire[1],endpoint_changed=name in dirty,precritical_released=name==case['precritical_decision']['net'] and case['precritical_decision']['eligible'],final_paths_equal_original=retained,final_paths_equal_cold=Counter(routes[0][name])==Counter(routes[1][name])))
 assert [sum(q[key] for q in netrows) for key in ('wire_resume','wire_cold')]==case['wire_pair']
 critical={}
 for mode,root,paths in zip(('resume','cold'),(workflow,cold),routes):
  report=root/'canonical/report_timing.setup.rpt';assert sha(report)==e['bindings'][str(report)];bindings[str(report)]=sha(report)
  first=report.read_text().split('#Path 2')[0]
  start=re.search(r'^Startpoint:\s*(\S+)',first,re.M)[1];endpoint=re.search(r'^Endpoint\s*:\s*(\S+)',first,re.M)[1]
  output=re.search(r'^out:(.+)\.outpad\[0\]$',endpoint)
  name=output[1] if output else None
  critical[mode]=dict(startpoint=start,endpoint=endpoint,output_net=name,output_net_endpoint_changed=name in dirty if name else None,output_net_precritical_released=name==case['precritical_decision']['net'],output_paths_equal_original=Counter(paths[name])==Counter(seed[name]) if name else None,reported_first_path=first)
 positives=sorted((q for q in netrows if q['wire_delta']>0),key=lambda q:(-q['wire_delta'],q['name']))
 summary={}
 for label,subset in [('final_old_paths',[q for q in netrows if q['final_paths_equal_original']]),('final_changed_paths',[q for q in netrows if not q['final_paths_equal_original']]),('endpoint_changed',[q for q in netrows if q['endpoint_changed']]),('endpoint_stable',[q for q in netrows if not q['endpoint_changed']])]:
  summary[label]=dict(nets=len(subset),signed_wire_delta=sum(q['wire_delta'] for q in subset),positive_wire_excess=sum(max(0,q['wire_delta']) for q in subset),negative_wire_savings=sum(min(0,q['wire_delta']) for q in subset))
 assert sum(q['wire_delta'] for q in netrows)==case['wire_pair'][0]-case['wire_pair'][1]
 rows.append(dict(width=w,index=i,cpd_pair=case['cpd_pair'],wire_pair=case['wire_pair'],failure=dict(cpd=not case['cpd_nonregression'],wire=not case['wire_nonregression']),critical=critical,wire_classes=summary,top_positive_wire_nets=positives[:10],all_net_wire_differences=netrows))
assert len(rows)==5 and all(sha(p)==h for p,h in bindings.items())
out=ROOT/'experiments/native_resume_cohort_failure_diagnosis_2026-10-07';out.mkdir(exist_ok=False)
result=dict(bindings=bindings,rows=rows,scope='Retrospective 5 failed cases from all12 development cohort. Exact wholeNET channel union span difference reproduces printed native wire. Final path equality to old seed is not proof of never processing a NET. Native critical report rounded, only terminal NET mapped; internal blocks not equated to packed NETs. No new routing, tuned threshold, causal proof or netgain.')
(out/'diagnosis.json').write_text(json.dumps(result,indent=2)+'\n')
print([(r['width'],r['index'],r['critical']['resume']['output_net'],r['critical']['resume']['output_paths_equal_original'],r['wire_classes']['final_old_paths']['signed_wire_delta'],r['wire_classes']['final_changed_paths']['signed_wire_delta']) for r in rows])
