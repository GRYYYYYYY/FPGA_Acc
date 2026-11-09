"""Full-NET exchange using an existing exact graph/floor context, no label inputs."""
import json,re,time,subprocess,sys
from array import array
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2]
def old_delay_for(q,name,paths,lookup,rc):
 ps=[p for p in paths[name] if p[0][0]==q['source'] and p[-1][0]==q['sink']];assert len(ps)==1
 return rc.initial(q['source'])+sum(rc.increments[lookup[u,v,sw]] for (u,_),(v,sw) in zip(ps[0],ps[0][1:]))
def exchange(ctx,ep,original,out,inventory):
 start=time.perf_counter();ep=Path(ep);out=Path(out);out.mkdir(exist_ok=False);cache_before=dict(ctx._cache);epoch_before=ctx.epoch;
 meta,_=ctx._validate(ep);graph=ctx.graph;digest=ctx.digest;f=ctx.fields;rc=ctx.rc;nodes=range(ctx.n);queries=meta['connections'];original=Path(original);paths=physical_paths(original);lookup={(u,f['dest_ranks'][s],f['switch_ids'][s]):s for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};span=[0]*len(nodes)
 inventory.validate(graph,digest)
 for n,(kind,loc) in inventory.nodes.items():
  if kind in ('CHANX','CHANY'):span[n]=1+int(loc['xhigh'])-int(loc['xlow'])+int(loc['yhigh'])-int(loc['ylow'])
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
 payload=out/'input.bin';binary=ROOT/'build/native_resume_shared_exchange_binary_cpp_2026-10-07/exchange';source=ROOT/'tools/native_resume_prototype/shared_exchange_binary_cpp/main.cpp';bindings={str(x):sha(x) for x in (ep,graph,original,report,binary,source,Path(__file__))}
 with payload.open('wb') as stream:
  def emit(a):
   values=array('Q',a);assert values.itemsize==8
   if sys.byteorder!='little':values.byteswap()
   stream.write(values.tobytes())
  emit([2026100703,len(nodes),len(f['edge_ids']),len(r['rows']),penalty])
  stream.write(ctx.graph_bytes);emit(span)
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
 finished=time.perf_counter();answers=list(map(json.loads,file.read_text().splitlines()));assert len(answers)==len(rows);records=[];owners={};old_owners={name:{n for path in ps for n,_ in path} for name,ps in paths.items() if ps}
 for idx,(answer,row) in enumerate(zip(answers,rows)):
  assert answer['index']==idx and len(answer['records'])==len(row['records']);name=row['net'];union=set();parents={}
  for actual,record in zip(answer['records'],row['records']):
   q=record['query'];assert actual['connection_id']==q['connection_id'];slots=actual['slots'];node=q['source'];union.add(node)
   for slot in slots:
    assert f['row_offsets'][node]<=slot<f['row_offsets'][node+1];v=f['dest_ranks'][slot];parent=(node,f['switch_ids'][slot]);assert v not in parents or parents[v]==parent;parents[v]=parent;node=v;union.add(node)
   assert node==q['sink'];edges=[f['edge_ids'][slot] for slot in slots];delay=rc.path(q['source'],q['sink'],edges);assert delay==actual['delay']<=old_delay_for(q,name,paths,lookup,rc)
   records.append(dict(q,answer=dict(physical_edge_ids=edges)))
  assert sum(span[n] for n in old_owners[name])==answer['old_wire'];assert sum(span[n] for n in union)==answer['new_wire']<=answer['old_wire'];owners[name]=union
 occ=Counter(n for union in owners.values() for n in union);assert all(v<=f['capacities'][n] for n,v in occ.items());assert len(records)==len(queries) and {q['connection_id'] for q in records}=={q['connection_id'] for q in queries};ctx._validate(ep);assert ctx._cache==cache_before and ctx.epoch==epoch_before;assert all(sha(f)==h for f,h in bindings.items())
 result=dict(records=records,bindings=bindings,conversion_seconds=prepared-start,compiled_child_seconds=finished-prepared,total_seconds=time.perf_counter()-start,selected_net_names=selected,all_target_endpoints_and_capacity_verified=True,unchanged_floor_cache=True)
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');return result
