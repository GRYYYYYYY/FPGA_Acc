"""Persistent source NET ownership linked to new preroute endpoint changes."""
import json,math,struct,sys
from pathlib import Path
from collections import defaultdict,Counter
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_owner_delta_features_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(line) for line in Path(p).read_text().splitlines()]
def main():
 assert sys.byteorder=='little';D.mkdir(exist_ok=False);source=E/'wbuart_track_aware_features_v1_2026-10-20/verification.json';proof=source.parent/'independent_verification_v1.json';H=E/'wbuart_preroute_heterograph_v1_2026-10-20/verification.json';design=E/'wbuart_owner_delta_CART_design_v1_2026-10-20/protocol.json'
 for p in [source,proof,design]:assert all(sha(path)==h for path,h in read(p)['bindings'].items())
 old=read(source);inputs={r['case']:r for r in read(H)['rows']};cache={};graphs={};rows=[];bindings={str(p):sha(p) for p in [source,proof,H,design,Path(__file__)]}
 for row in old['rows']:
  h=inputs[row['case']];digest=h['graph_sha256'];channels=set(read(row['resource_ids']))
  if digest not in graphs:
   gd=H.parent/'graphs'/digest;edges=lines(gd/'physical_edges.jsonl');assert all(e['edge_id']==i for i,e in enumerate(edges));nodes={n['id']:n for n in lines(gd/'RR_nodes.jsonl')};graphs[digest]=(edges,nodes)
  edges,nodes=graphs[digest];source_path=row['source_frame']
  if source_path not in cache:
   frame=read(source_path);assert frame['graph_sha256']==digest;records={q['connection_id']:q for q in frame['records']};assert len(records)==len(frame['records']);refs=defaultdict(set);owners=defaultdict(set);fanout=Counter(q['net_id'] for q in records.values())
   for cid,q in records.items():
    cursor=q['source'];seen={cursor};assert nodes[cursor]['type']=='SOURCE' and nodes[q['sink']]['type']=='SINK'
    for eid in q['answer']['physical_edge_ids']:
     edge=edges[eid];assert edge['source']==cursor;cursor=edge['sink'];assert cursor not in seen;seen.add(cursor)
    assert cursor==q['sink']
    for node in seen&channels:refs[node].add(cid);owners[node].add(q['net_id'])
   ledger={int(n):c for n,c in frame['ledger'].items()};assert all(len(owners[n])<=1 and ledger.get(n,0)==len(owners[n]) for n in channels);directory=D/'source_indices'/sha(source_path);directory.mkdir(parents=True);index=directory/'owners.jsonl'
   with index.open('x') as f:
    for node in sorted(channels):f.write(json.dumps({'RR':node,'NET':next(iter(owners[node])) if owners[node] else None,'old_ref_CIDs':sorted(refs[node])},separators=(',',':'))+'\n')
   cache[source_path]=(records,refs,owners,fanout,str(index));bindings[str(index)]=sha(index);bindings[source_path]=sha(source_path)
  records,refs,owners,fanout,index=cache[source_path];target_path=Path(h['directory'])/'NET_RR_incidence.jsonl';target={q['connection_id']:q for q in lines(target_path)};assert set(target)==set(records);changed=set();sink_moves=Counter();source_moves=set();net_changes=Counter()
  for cid,q in records.items():
   t=target[cid];assert (t['full_connection_id'],t['net_id'])==(q['full_connection_id'],q['net_id']);net=q['net_id'];source_move=t['source']!=q['source'];sink_move=t['sink']!=q['sink'];sink_moves[net]+=sink_move
   if source_move:source_moves.add(net)
   if source_move or sink_move:changed.add(cid);net_changes[net]+=1
  ids=read(row['resource_ids']);original=Path(row['matrix']).read_bytes();assert len(original)==len(ids)*31*8;directory=D/row['case'];directory.mkdir(parents=True);p=directory/'raw_features.f64';facts=[]
  with p.open('xb') as f:
   for i,node in enumerate(ids):
    net=next(iter(owners[node])) if owners[node] else None
    raw=[fanout[net],len(refs[node]),int(net in source_moves),sink_moves[net],net_changes[net],len(refs[node]&changed),int(net_changes[net]>0)] if net is not None else [0]*7;values=[math.log1p(raw[j]) if j in [0,1,3,4,5] else raw[j] for j in range(7)];f.write(original[i*248:(i+1)*248]);f.write(struct.pack('<7d',*values));facts.append({'RR':node,'raw_owner_context':raw})
  witness=directory/'owner_context.json';witness.write_text(json.dumps(facts,separators=(',',':'))+'\n');rows.append({**row,'matrix':str(p),'columns':38,'original31_matrix':row['matrix'],'source_index':index,'target_incidence':str(target_path),'owner_context':str(witness),'changed_CIDs':len(changed),'changed_NETs':len(net_changes),'source_moved_NETs':len(source_moves)})
  for path in [p,witness,target_path]:bindings[str(path)]=sha(path)
  print('OWNER_DELTA_FEATURES',row['case'],len(changed),len(net_changes),flush=True)
 columns=['log1p old owner fanout','log1p old CID refcount','owner source moved','log1p owner sink moved CIDs','log1p owner endpoint changed CIDs','log1p changed old CID references','owner any endpoint moved'];(D/'verification.json').write_text(json.dumps({'status':'ALL9_PRIOR_OWNER_ENDPOINT_DELTA38_INPUTS_PRODUCED','rows':rows,'columns':old['columns']+columns,'bindings':bindings,'target_labels_read':False,'scope':'Known prior physical paths and current preroute endpoints only; all prior CHANNEL owners unit-capacity, no target route/candidate input. Owner/CID joins are not model features.'},indent=2)+'\n')
if __name__=='__main__':main()
