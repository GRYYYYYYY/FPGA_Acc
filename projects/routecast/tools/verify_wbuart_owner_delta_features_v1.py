"""Independent XML paths, NET set ownership and perCID endpoint-delta reference."""
import json,math,struct,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_owner_delta_features_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'verification.json';v=read(p);H=read(E/'wbuart_preroute_heterograph_v1_2026-10-20/verification.json');assert len(v['rows'])==9 and len(v['columns'])==38 and not v['target_labels_read'];assert all(sha(path)==h for path,h in v['bindings'].items());assert all(sha(path)==h for path,h in H['bindings'].items());graphs={};sources={};count=0;path_count=0
 for r in v['rows']:
  info=next(h for h in H['rows'] if h['case']==r['case']);digest=info['graph_sha256']
  if digest not in graphs:
   graph=next(h['graph'] for h in H['graphs'] if Path(h['directory']).name==digest);arcs=[]
   for _,e in ET.iterparse(graph):
    if e.tag=='edge':arcs.append((int(e.get('src_node')),int(e.get('sink_node'))));e.clear()
   graphs[digest]=arcs
  ids=read(r['resource_ids']);channels=set(ids);source=r['source_frame']
  if source not in sources:
   frame=read(source);old={q['connection_id']:q for q in frame['records']};assert len(old)==len(frame['records']);arcs=graphs[digest];net_nodes=defaultdict(set);node_cids=defaultdict(set);net_cids=defaultdict(set)
   for cid,q in old.items():
    current=q['source'];nodes={current}
    for edge in q['answer']['physical_edge_ids']:
     assert type(edge) is int and 0<=edge<len(arcs);a,b=arcs[edge];assert a==current and b not in nodes;current=b;nodes.add(b)
    assert current==q['sink'];owned=nodes&channels;net_nodes[q['net_id']].update(owned);net_cids[q['net_id']].add(cid)
    for n in owned:node_cids[n].add(cid)
    path_count+=1
   owners={n:[net for net,owned in net_nodes.items() if n in owned] for n in ids};ledger={int(n):c for n,c in frame['ledger'].items()};assert all(len(owners[n])==ledger.get(n,0)<=1 for n in ids);sources[source]=(old,owners,node_cids,net_cids)
  old,owners,node_cids,net_cids=sources[source];new={q['connection_id']:q for q in map(json.loads,Path(r['target_incidence']).read_text().splitlines())};assert set(new)==set(old);changed={};sinks={};source_moved={}
  for net,cids in net_cids.items():
   for cid in cids:assert (old[cid]['full_connection_id'],old[cid]['net_id'])==(new[cid]['full_connection_id'],new[cid]['net_id'])
   changed[net]={c for c in cids if (old[c]['source'],old[c]['sink'])!=(new[c]['source'],new[c]['sink'])};sinks[net]={c for c in cids if old[c]['sink']!=new[c]['sink']};source_moved[net]=any(old[c]['source']!=new[c]['source'] for c in cids)
  assert sum(map(len,changed.values()))==r['changed_CIDs'] and sum(bool(x) for x in changed.values())==r['changed_NETs'];index=[json.loads(x) for x in Path(r['source_index']).read_text().splitlines()];assert index==[{'RR':n,'NET':owners[n][0] if owners[n] else None,'old_ref_CIDs':sorted(node_cids[n])} for n in sorted(ids)];facts=read(r['owner_context']);assert [q['RR'] for q in facts]==ids;before=Path(r['original31_matrix']).read_bytes();after=Path(r['matrix']).read_bytes();assert len(before)==len(ids)*248 and len(after)==len(ids)*304
  for i,n in enumerate(ids):
   if owners[n]:
    net=owners[n][0];raw=[len(net_cids[net]),len(node_cids[n]),int(source_moved[net]),len(sinks[net]),len(changed[net]),len(node_cids[n]&changed[net]),int(bool(changed[net]))]
   else:raw=[0]*7
   assert facts[i]['raw_owner_context']==raw and after[i*304:i*304+248]==before[i*248:(i+1)*248];values=struct.unpack('<7d',after[i*304+248:(i+1)*304]);expected=tuple(math.log1p(x) if j in [0,1,3,4,5] else float(x) for j,x in enumerate(raw));assert values==expected;count+=1
  print('OWNER_DELTA_INDEPENDENT_PASS',r['case'],flush=True)
 out=D/'independent_verification_v1.json';out.write_text(json.dumps({'status':'ALL9_OLD_XML_OWNERS_CID_REFERENCES_ENDPOINT_DELTAS_AND31_PREFIXES_VERIFIED','resource_rows':count,'source_paths':path_count,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__),str(E/'wbuart_preroute_heterograph_v1_2026-10-20/verification.json'):sha(E/'wbuart_preroute_heterograph_v1_2026-10-20/verification.json'),**{r['graph']:sha(r['graph']) for r in H['graphs']}},'scope':'Source old paths and current preroute endpoint context only; no labels/current route prediction or utility claim.'},indent=2)+'\n');print('ALL_OWNER_DELTA_INPUTS_VERIFIED',count,path_count)
if __name__=='__main__':main()
