"""Same frozen additive ordinary baseline recovery after terminal audit failure.

No native quality labels opened. Full graph, all8998groups/15138connections.
Durable per-net diagnostic journal and pre-audit prediction preserve evidence.
"""
import json,time,shutil,subprocess,collections
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from cached_bound_rc import CachedBoundRC
from prepared_csr import write
from physical_prediction_audit import audit
from rr_occupancy import Occupancy
from connection_golden import Result
out=Path('experiments/koios_cpp_recovery_2026-10-05');failed=Path('experiments/koios_full_cached_rc_2026-10-04');binary=Path('build/routecast_csr_direct').resolve()
if out.exists():raise ValueError('fresh output required')
prior=json.loads((failed/'protocol.json').read_text());inputs=prior['inputs'];assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
e=json.loads(Path(inputs['endpoints']['path']).read_text());groups={}
for row in e['connections']:groups.setdefault(row['net_id'],[]).append(row)
assert len(groups)==8998 and len(e['connections'])==15138
out.mkdir();(out/'source').mkdir()
for f in Path('tools').glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
for f in Path('include').glob('*.hpp'):shutil.copyfile(f,out/'source'/f.name)
shutil.copyfile('tools/csr_consumer/direct_main.cpp',out/'source/direct_main.cpp');shutil.copy2(binary,out/'routecast_csr_direct')
p={'inputs':inputs,'prior_failed_protocol_sha256':sha(failed/'protocol.json'),'source_sha256':{f.name:sha(f) for f in (out/'source').iterdir()},'binary_sha256':sha(out/'routecast_csr_direct'),'connections':15138,'nets':8998,'objective':prior['objective'],'order':prior['order'],'node_budget':'entire physical graph','recovery_change':'ordinary C++ directarray canonical Dijkstra using exact cached additive CSR; durable journal/preaudit saving; no cost/geometry/pressure change','scope':'singleKoiosdesign/seed frozen transfer, not familygeneralization/qualitybenefit/hardwareclaim'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');print(json.dumps({'stage':'graph_load'}),flush=True)
start=time.monotonic();g=read_rr_graph(inputs['rr_graph.xml']['path']);load=time.monotonic()-start
identity={'graph_sha256':g.sha256,'table_sha256':inputs['rr_indexed_data.echo']['sha256'],'bindings_sha256':inputs['routecast_node_cost_indices.csv']['sha256']}
start=time.monotonic();model=CachedBoundRC(g,Path(inputs['rr_indexed_data.echo']['path']).read_text(),Path(inputs['routecast_node_cost_indices.csv']['path']).read_text(),identity);prep=time.monotonic()-start
start=time.monotonic();manifest=write(model,out/'csr');export=time.monotonic()-start
(out/'preparation.json').write_text(json.dumps({'graph_load_s':load,'cost_preparation_s':prep,'csr_export_s':export,'manifest_sha256':sha(out/'csr/manifest.json'),'context_sha256':manifest['context_sha256'],'cache_entries':model.cache_entries,'all_edge_cost_queries':model.edge_cost_queries},indent=2)+'\n');del model
print(json.dumps({'stage':'prepared','load_s':load,'prep_s':prep,'export_s':export}),flush=True)
probe=Path('experiments/koios_cached_rc_probe_2026-10-04');pr=json.loads((probe/'receipt.json').read_text());assert sha(probe/'prediction.json')==pr['outputs']['prediction.json'];gold={v['connection_id']:v for v in json.loads((probe/'prediction.json').read_text())['connections']}
worker=subprocess.Popen([str((out/'routecast_csr_direct').resolve()),str(out/'csr'),'--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
ledger=Occupancy(g);rows=[];visits=0;settled=0;failed_count=0;matched=0;start=time.monotonic()
with (out/'net_results.jsonl').open('w') as journal:
 for i,(net,cohort) in enumerate(sorted(groups.items()),1):
  sources={v['source'] for v in cohort};assert len(sources)==1;source=next(iter(sources));targets=sorted({v['sink'] for v in cohort})
  worker.stdin.write(' '.join(map(str,[source,*targets]))+'\n');worker.stdin.flush();result=json.loads(worker.stdout.readline());assert not result['budget_exhausted'];assert set(result['paths'])<=set(map(str,targets))
  # Save witness before validation or mutable bookkeeping can reject it.
  journal.write(json.dumps({'net_id':net,'source':source,'result':result})+'\n');journal.flush()
  visits+=result['edge_visits'];settled+=result['settled_nodes']
  for row in cohort:
   path=result['paths'].get(str(row['sink']));method='cached_bound_rc' if path is not None else 'failed'
   if path is not None:assert ledger.update(row['connection_id'],1,net,source,row['sink'],path)==Result.COMMITTED
   else:failed_count+=1
   if row['connection_id'] in gold:assert path==gold[row['connection_id']]['physical_edge_ids'];matched+=1
   rows.append({**row,'physical_edge_ids':path,'method':method})
  if i%100==0:print(json.dumps({'stage':'search','nets':i,'connections':len(rows),'failed':failed_count}),flush=True)
worker.stdin.close();assert worker.wait()==0;query=time.monotonic()-start;assert len(rows)==15138 and matched==741
prediction={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'requested':len(rows),'completed':len(rows)-failed_count,'methods':dict(collections.Counter(row['method'] for row in rows))}
# Preserve complete output even if final validation fails.
for name,data in [('prediction.json',prediction),('endpoints.json',e)]: (out/name).write_text(json.dumps(data)+'\n')
checked=audit(g,e,prediction);assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
receipt={'protocol_sha256':sha(out/'protocol.json'),'graph_load_s':load,'preparation_s':prep,'csr_export_s':export,'query_ledger_s':query,'edge_visits':visits,'settled_nodes':settled,'failed_connections':failed_count,'exact_prior_net2_probe_paths':matched,'audit':checked,'inputs_unchanged':True,'preparation_sha256':sha(out/'preparation.json'),'manifest_sha256':sha(out/'csr/manifest.json'),'binary_sha256':sha(out/'routecast_csr_direct'),'outputs':{name:sha(out/name) for name in ('prediction.json','endpoints.json','net_results.jsonl')}};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
