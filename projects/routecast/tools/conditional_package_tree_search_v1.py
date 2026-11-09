"""Single exact raw-search attempt against an explicit unique-NET capacity ledger."""
from soft_demand_workspace_bridge_v1 import Search

def owned(candidate,fields,slots):
 ns={r['source'] for r in candidate['records']}
 for r in candidate['records']:ns.update(fields['dest_ranks'][slots[e]] for e in r['answer']['physical_edge_ids'])
 return ns

def attempt(template,fields,nodes,rc,binary,slots,outside,usage,extra=()):
 caps=fields['capacities'];source=next(iter(template.values()))['source'];assert all(r['source']==source for r in template.values());taboo={n for n,cap in enumerate(caps) if outside[n]+usage[n]>=cap};taboo.update(extra);info=dict(forbidden_nodes=len(taboo),connections=len(template))
 if source in taboo:return None,dict(info,reason='FORBIDDEN_SOURCE',failed_CIDs=sorted(template))
 modified=dict(fields);modified['capacities']=[0 if n in taboo else max(0,cap-outside[n]-usage[n]) for n,cap in enumerate(caps)];search=Search(modified,rc,binary);search.prepare({},0)
 try:
  dist,parent,settled=search.search(source,{r['sink'] for r in template.values()});bad=sorted(cid for cid,r in template.items() if r['sink'] not in settled or dist[r['sink']]>r['budget_integer'])
  if bad:return None,dict(info,reason='UNREACHABLE_OR_BUDGET',failed_CIDs=bad,failed_details=[dict(connection_id=cid,sink=template[cid]['sink'],settled=template[cid]['sink'] in settled,shortest_delay=int(dist[template[cid]['sink']]) if template[cid]['sink'] in settled else None,budget=template[cid]['budget_integer']) for cid in bad])
  records=[];parents={}
  for cid,old in sorted(template.items()):
   u=old['sink'];edges=[];seen=set()
   while u!=source:
    assert u not in seen and u not in taboo;seen.add(u);u,slot=parent[u];edges.append(fields['edge_ids'][slot])
   edges.reverse();delay=rc.path(source,old['sink'],edges);assert delay==dist[old['sink']]<=old['budget_integer'];u=source
   for eid in edges:
    v=fields['dest_ranks'][slots[eid]]
    if nodes[v].get('type')!='SINK':assert v not in parents or parents[v]==(u,eid);parents[v]=(u,eid)
    u=v
   records.append(dict(old,answer=dict(status='FOUND',physical_edge_ids=edges,delay=delay)))
  candidate=dict(records=records);assert not owned(candidate,fields,slots)&taboo
  return candidate,dict(info,reason=None)
 finally:search.close()
