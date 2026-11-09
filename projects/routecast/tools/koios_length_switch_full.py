"""Full matched length+switch control on authenticated physical CSR.
No native labels. Durable witnesses before independent physical XML audit.
"""
import json,time,shutil,subprocess,collections
from pathlib import Path
from array import array
from pre_route_endpoints import sha
from prepared_csr import read,U64
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
out=Path('experiments/koios_length_switch_full_2026-10-05');prepared=Path('experiments/koios_length_switch_csr_2026-10-05');parent=Path('experiments/koios_cpp_resume_2026-10-05');binary=(parent/'routecast_csr_direct').resolve()
if out.exists():raise ValueError('fresh output required')
p=json.loads((parent/'protocol.json').read_text());prep=json.loads((prepared/'preparation_receipt.json').read_text());inputs=p['inputs'];assert all(sha(v['path'])==v['sha256'] for v in inputs.values());assert sha(prepared/'manifest.json')==prep['manifest_sha256'];assert sha(binary)==p['binary_sha256']
e=json.loads(Path(inputs['endpoints']['path']).read_text());groups={}
for row in e['connections']:groups.setdefault(row['net_id'],[]).append(row)
assert len(groups)==8998 and len(e['connections'])==15138
out.mkdir();(out/'source').mkdir();shutil.copy2(binary,out/'routecast_csr_direct');assert (out/'routecast_csr_direct').stat().st_mode&0o111
for f in Path('tools').glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
shutil.copytree('experiments/koios_cpp_recovery_2026-10-05/source',out/'binary_source')
protocol={'inputs':inputs,'source_sha256':{f.name:sha(f) for f in (out/'source').iterdir()},'binary_sha256':sha(out/'routecast_csr_direct'),'control_specification_sha256':sha('experiments/koios_length_switch_control_protocol_2026-10-05/protocol.json'),'preparation_sha256':sha(prepared/'preparation_receipt.json'),'manifest_sha256':prep['manifest_sha256'],'objective':'exact original rr_length_switch additive cost; full physical graph','order':p['order'],'connections':15138,'nets':8998,'binary_source_sha256':{f.name:sha(f) for f in (out/'binary_source').iterdir()},'scope':'matched length+switch all frozen ordinary additive cohort, no native quality labels opened; durable CSR path journal and independent original XML audit'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
print(json.dumps({'stage':'csr_verify'}),flush=True);start=time.monotonic();m,f=read(prepared,inputs['rr_graph.xml']['sha256'],prep['context_sha256']);verify=time.monotonic()-start
ids=f['node_ids'];rank={n:i for i,n in enumerate(ids)};es=array('Q',[0])*m['edges'];ed=array('Q',[0])*m['edges'];slot_for=array('Q',[0])*m['edges']
for r,source in enumerate(ids):
 for slot in range(f['row_offsets'][r],f['row_offsets'][r+1]):eid=f['edge_ids'][slot];es[eid]=source;ed[eid]=ids[f['dest_ranks'][slot]];slot_for[eid]=slot
worker=subprocess.Popen([str((out/'routecast_csr_direct').resolve()),str(prepared),'--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
rows=[];occupancy=collections.Counter();visits=0;settled=0;failed=0;matched=0;start=time.monotonic()
with (out/'net_results.jsonl').open('w') as journal:
 for i,(net,cohort) in enumerate(sorted(groups.items()),1):
  sources={v['source'] for v in cohort};assert len(sources)==1;source=next(iter(sources));targets=sorted({v['sink'] for v in cohort});assert f['types'][rank[source]]==0
  worker.stdin.write(' '.join(map(str,[source,*targets]))+'\n');worker.stdin.flush();result=json.loads(worker.stdout.readline());assert not result['budget_exhausted'];assert set(result['paths'])==set(map(str,targets)), 'whole-net control must complete before occupancy commit';journal.write(json.dumps({'net_id':net,'source':source,'result':result})+'\n');journal.flush();touched=set();visits+=result['edge_visits'];settled+=result['settled_nodes']
  for row in cohort:
   path=result['paths'].get(str(row['sink']));method='rr_length_switch' if path is not None else 'failed'
   if path is None:failed+=1
   else:
    node=source;seen={node}
    for eid in path:
     assert type(eid) is int and 0<=eid<m['edges'] and es[eid]==node and f['costs'][slot_for[eid]]!=U64
     node=ed[eid];assert node not in seen and f['capacities'][rank[node]]>0;seen.add(node)
    assert node==row['sink'] and f['types'][rank[node]]==1;touched.update(seen)
   rows.append({**row,'physical_edge_ids':path,'method':method})
  occupancy.update(touched)
  if i%100==0:print(json.dumps({'stage':'search','nets':i,'connections':len(rows),'failed':failed}),flush=True)
worker.stdin.close();assert worker.wait()==0;query=time.monotonic()-start;assert len(rows)==15138
prediction={'physical_graph_sha256':inputs['rr_graph.xml']['sha256'],'connections':rows,'node_occupancy':{str(n):v for n,v in occupancy.items()},'requested':len(rows),'completed':len(rows)-failed,'methods':dict(collections.Counter(row['method'] for row in rows))}
for name,data in [('prediction.json',prediction),('endpoints.json',e)]: (out/name).write_text(json.dumps(data)+'\n')
del f,es,ed,slot_for,rank,ids;print(json.dumps({'stage':'independent_XML_audit'}),flush=True);start=time.monotonic();g=read_rr_graph(inputs['rr_graph.xml']['path']);checked=audit(g,e,prediction);audit_s=time.monotonic()-start;assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
receipt={'protocol_sha256':sha(out/'protocol.json'),'prepared_stage_costs':prep,'csr_verify_s':verify,'query_ledger_s':query,'independent_XML_audit_s':audit_s,'edge_visits':visits,'settled_nodes':settled,'failed_connections':failed,'audit':checked,'inputs_unchanged':True,'binary_sha256':sha(out/'routecast_csr_direct'),'outputs':{name:sha(out/name) for name in ('prediction.json','endpoints.json','net_results.jsonl')}};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
