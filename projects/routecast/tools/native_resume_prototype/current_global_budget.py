"""Whole-NET conditioned minimum-delay trees under own current global wire budget."""
import json,re,struct,subprocess,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha

def repair(ctx,inventory,endpoint,records,report,budget,out):
 start=time.perf_counter();out=Path(out);out.mkdir(exist_ok=False);meta=json.loads(Path(endpoint).read_text());ctx._validate(endpoint);f=ctx.fields;rc=ctx.rc
 bindings={str(p):sha(p) for p in (Path(endpoint),Path(report),ctx.binary,Path(__file__))};inventory.validate(ctx.graph,ctx.digest)
 records=json.loads(json.dumps(records));groups={}
 for q in records:groups.setdefault(meta['net_names'][str(q['net_id'])],[]).append(q)
 arc={f['edge_ids'][s]:(u,f['dest_ranks'][s],f['switch_ids'][s]) for u in range(ctx.n) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])}
 def union(qs):
  us=set();parents={}
  for q in qs:
   u=q['source'];us.add(u)
   for eid in q['answer']['physical_edge_ids']:
    previous,v,sw=arc[eid];assert previous==u and v not in (q['source'],)
    if v in parents:assert parents[v]==(u,sw)
    parents[v]=(u,sw);us.add(v);u=v
   assert u==q['sink']
  return us
 spans={n:1+int(loc['xhigh'])-int(loc['xlow'])+int(loc['yhigh'])-int(loc['ylow']) for n,(kind,loc) in inventory.nodes.items() if kind in ('CHANX','CHANY')}
 wire=lambda us:sum(spans.get(n,0) for n in us)
 owners={name:union(qs) for name,qs in groups.items()};occ=Counter(n for us in owners.values() for n in us);total=sum(wire(us) for us in owners.values());assert total<=budget and all(v<=f['capacities'][n] for n,v in occ.items())
 selected=[]
 for name,port in re.findall(r'^(\S+)\.(inpad|out|Q)\[\d+\]\s+\(',Path(report).read_text().split('#Path 2')[0],re.M):
  if name in groups and name not in selected:selected.append(name)
 initial=total;rows=[]
 (out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,selected_net_names=selected,budget=budget,initial_wire=initial,policy='Current own report first worst setup path drivers incl Q. Process NETs in report order, release whole NET and freeze all other current owner unions. Grouped-source additive integer RC shortest tree; accept only some strict delay improvement, no sink delay increase, global wire <= own first native wire. Sequential occupancy update; cold-independent.'),indent=2)+'\n')
 for index,name in enumerate(selected):
  qs=groups[name];oldunion=owners[name];other=Counter(occ);other.subtract(oldunion);caps=[max(0,f['capacities'][n]-other.get(n,0)) for n in range(ctx.n)];assert all(caps[q['source']]>0 and caps[q['sink']]>0 for q in qs)
  payload=out/f'net_{index}.bin'
  with payload.open('wb') as stream:
   for values in ([0x5243464c4f4f5231,ctx.n,len(f['edge_ids']),len(qs)],f['row_offsets'],f['dest_ranks'],rc.increments,caps,ctx.initial,[v for q in qs for v in (q['connection_id'],q['source'],q['sink'])]):
    for v in values:stream.write(struct.pack('<Q',v))
  file=out/f'net_{index}.jsonl'
  with file.open('w') as stream:subprocess.run([str(ctx.binary),str(payload)],stdout=stream,stderr=subprocess.PIPE,check=True,timeout=120)
  answers={a['connection_id']:a for a in map(json.loads,file.read_text().splitlines())};trials=[];delays=[]
  for q in qs:
   a=answers[q['connection_id']];assert a['minimum_integer'] is not None
   edges=[f['edge_ids'][s] for s in a['slots']];assert rc.path(q['source'],q['sink'],edges)==a['minimum_integer']
   old=rc.path(q['source'],q['sink'],q['answer']['physical_edge_ids']);delays.append(dict(connection_id=q['connection_id'],old_integer=old,new_integer=a['minimum_integer']))
   trials.append(dict(q,answer=dict(physical_edge_ids=edges)))
  newunion=union(trials);assert all(other.get(n,0)+1<=f['capacities'][n] for n in newunion)
  trialtotal=total-wire(oldunion)+wire(newunion);accepted=all(x['new_integer']<=x['old_integer'] for x in delays) and any(x['new_integer']<x['old_integer'] for x in delays) and trialtotal<=budget
  rows.append(dict(net=name,delays=delays,old_wire=wire(oldunion),new_wire=wire(newunion),previous_total_wire=total,trial_total_wire=trialtotal,accepted=accepted,payload_sha256=sha(payload),output_sha256=sha(file),old_union=sorted(oldunion),new_union=sorted(newunion),other_occupancy={str(n):v for n,v in other.items() if v},trial_records=trials))
  if accepted:
   groups[name]=trials;owners[name]=newunion;occ=other;occ.update(newunion);total=trialtotal
 result=dict(records=[q for qs in groups.values() for q in qs],rows=rows,bindings=bindings,initial_wire=initial,final_wire=total,budget=budget,total_seconds=time.perf_counter()-start,scale=rc.scale)
 assert all(sha(p)==h for p,h in bindings.items());(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');return result
