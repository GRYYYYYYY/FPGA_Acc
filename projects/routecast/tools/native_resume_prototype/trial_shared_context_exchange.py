"""Fresh graph conversion, compiled full-NET exchange and exact Python parity."""
import json,sys,time,subprocess,re,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reusable_rr_floor_context import ReusableRRFloors
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];w,i=map(int,sys.argv[1:]);out=ROOT/f'experiments/native_resume_shared_context_exchange_w{w}_m{i}_2026-10-07';out.mkdir(exist_ok=False);start=time.perf_counter();ref=ROOT/f'experiments/native_resume_full_exchange_delay_0.01_w{w}_m{i}_2026-10-07';ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';ctx=ReusableRRFloors(ep,ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'floor_context');floor=ctx.query(ep);cache_before=dict(ctx._cache);floor_done=time.perf_counter();meta,_=ctx._validate(ep);graph=ctx.graph;digest=ctx.digest;f=ctx.fields;rc=ctx.rc;nodes=range(ctx.n);queries=meta['connections'];original=ROOT/f'experiments/native_resume_singlepass_floor_w{w}_m{i}_workflow_2026-10-07/canonical/design.route';paths=physical_paths(original);lookup={(u,f['dest_ranks'][s],f['switch_ids'][s]):s for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};span=[0]*len(nodes)
for _,node in ET.iterparse(graph,events=('end',)):
 if node.tag=='node':
  if node.get('type') in ('CHANX','CHANY'):
   loc=node.find('loc');span[int(node.get('id'))]=1+int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))
  node.clear()
report=original.parent/'report_timing.setup.rpt';selected=[]
for name,port in re.findall(r'^(\S+)\.(inpad|out)\[\d+\]\s+\(',report.read_text().split('#Path 2')[0],re.M):
 if name in paths and paths[name] and name not in selected:selected.append(name)
rank=sorted((name for name,ps in paths.items() if ps),key=lambda name:(-sum(span[n] for n in {n for path in paths[name] for n,_ in path}),name))
selected.extend(name for name in rank if name not in selected)
rows=[]
for name in selected:
 qs=[q for q in queries if meta['net_names'][str(q['net_id'])]==name]
 def old_delay(q):
  path=[p for p in paths[name] if p[0][0]==q['source'] and p[-1][0]==q['sink']];assert len(path)==1
  return rc.initial(q['source'])+sum(rc.increments[lookup[u,v,sw]] for (u,_),(v,sw) in zip(path[0],path[0][1:]))
 qs=sorted(qs,key=lambda q:(-old_delay(q),q['connection_id']));rows.append(dict(net=name,records=[dict(query=q) for q in qs]))
r=dict(rows=rows)
penalty=rc.scale//10**11;assert penalty*10**11==rc.scale
payload=out/'input.txt';binary=ROOT/'build/native_resume_shared_exchange_cpp_2026-10-07/exchange';source=ROOT/'tools/native_resume_prototype/shared_exchange_cpp/main.cpp';bindings={str(x):sha(x) for x in (ep,graph,original,report,binary,source,Path(__file__))}
with payload.open('w') as stream:
 def emit(a):stream.write(' '.join(map(str,a))+'\n')
 emit([2026100702,len(nodes),len(f['edge_ids']),len(r['rows']),penalty])
 for a in (f['row_offsets'],f['dest_ranks'],rc.increments,f['capacities'],[rc.initial(n) for n in range(len(nodes))],span):emit(a)
 for row in r['rows']:
  qs=[x['query'] for x in row['records']];initial_paths={}
  for q in qs:
   ps=[path for path in paths[row['net']] if path[0][0]==q['source'] and path[-1][0]==q['sink']];assert len(ps)==1;initial_paths[q['connection_id']]=[lookup[u,v,sw] for (u,_),(v,sw) in zip(ps[0],ps[0][1:])]
  ordered=sorted(qs,key=lambda q:(-sum(rc.increments[s] for s in initial_paths[q['connection_id']])-rc.initial(q['source']),q['connection_id']));assert qs==ordered
  emit([len(qs),qs[0]['source']])
  for q in qs:
   slots=initial_paths[q['connection_id']];emit([q['connection_id'],q['sink'],len(slots),*slots])
prepared=time.perf_counter();file=out/'output.jsonl'
with file.open('w') as stream:subprocess.run([str(binary),str(payload)],stdout=stream,stderr=subprocess.PIPE,check=True,timeout=120)
finished=time.perf_counter();expected_receipt=json.loads((ref/'receipt.json').read_text());r=expected_receipt;bindings[str(ref/'receipt.json')]=sha(ref/'receipt.json');answers=list(map(json.loads,file.read_text().splitlines()));assert len(answers)==len(r['rows']);count=0
for idx,(a,row) in enumerate(zip(answers,r['rows'])):
 assert a['index']==idx and a['attempts']==row['attempts'];assert a['old_wire']==row['old_wire'] and a['new_wire']==row['new_wire'];assert len(a['records'])==len(row['records'])
 for actual,expected in zip(a['records'],row['records']):
  assert actual['connection_id']==expected['query']['connection_id'];assert actual['delay']==expected['conditional_integer'];assert [f['edge_ids'][s] for s in actual['slots']]==expected['physical_edge_ids'];count+=1
assert count==len(queries);ctx._validate(ep);assert ctx._cache==cache_before and ctx.epoch==1;assert all(sha(f)==h for f,h in bindings.items());bindings.update({str(payload):sha(payload),str(file):sha(file)});result=dict(bindings=bindings,connections=count,all_decisions_paths_and_delays_exact=True,floor_context_and_query_seconds=floor_done-start,exchange_conversion_seconds=prepared-floor_done,conversion_seconds=prepared-start,compiled_child_seconds=finished-prepared,total_conversion_query_parity_seconds=time.perf_counter()-start,python_reference_seconds=r['total_seconds'],scope='Fresh complete graph export and one compiled process; exact per-attempt decision and full physical-path parity to prior Python/native-verified policy. Independent current-snapshot schedule; floor/query and exchange share one graph/RC object, cache unchanged. No live durable/concurrent context, no native rerun or complete end-to-end acceleration claim. Original candidate and reference acquisition excluded.');(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print({k:v for k,v in result.items() if k!='bindings'})
