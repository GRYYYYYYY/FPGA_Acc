import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';release_root=base/'native_move_release_contexts_2026-10-06';receipt=json.loads((release_root/'receipt.json').read_text());resource_receipt=json.loads((base/'native_candidate_resource_frames_2026-10-06/receipt.json').read_text());out=base/'native_complete_move_queries_2026-10-06';out.mkdir();summaries=[];maps={}
def locations(p):
 return {int(f[-1][1:]):tuple(map(int,f[1:5])) for l in p.read_text().splitlines() if len(f:=l.split())==6 and f[-1].startswith('#')}
for frame in receipt['frames']:
 design=frame['design'];step=frame['step'];p=release_root/f'{design}_{step}.json';assert sha(p)==frame['sha256'];released=json.loads(p.read_text());context_path=Path(released['source_context']);assert sha(context_path)==released['source_context_sha256'];ctx=json.loads(context_path.read_text());assert all(sha(f)==h for f,h in ctx['inputs_sha256'].items());cwd=root/'work/native_candidate_resource_frames_2026-10-06'/design;table=cwd/f'state_{step}.tsv';place=cwd/f'state_{step}.place';locs=locations(place);pins=[list(map(int,l.split('\t')[:6])) for l in table.read_text().splitlines()[2:]];command=next(r['command'] for r in resource_receipt['results'] if r['design']==design);graph=Path(command[command.index('--read_rr_graph')+1])
 if design not in maps:
  rr={};classes={};stack=[]
  for event,e in ET.iterparse(graph,events=('start','end')):
   if event=='start':stack.append(e);continue
   xml_parent=stack[-2].tag if len(stack)>1 else None
   if e.tag=='node' and xml_parent=='rr_nodes' and e.get('type') in ('SOURCE','SINK'):
    l=e.find('loc');key=(int(l.get('xlow')),int(l.get('ylow')),int(l.get('layer','0')),int(l.get('ptc')),e.get('type'));assert key not in classes;classes[key]=int(e.get('id'));rr[int(e.get('id'))]=key
   if (e.tag,xml_parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches')):stack[-2].remove(e);e.clear()
   stack.pop()
  maps[design]=(rr,classes)
 rr,classes=maps[design];moves=[]
 for move in released['moves']:
  a,b=move['pair'];moved=locs.copy();moved[a],moved[b]=moved[b],moved[a];dirty=set(move['dirty_native_nets']);queries=[]
  for net,pin,source_block,sink_block,source_rr,sink_rr in pins:
   if net not in dirty:continue
   endpoints=[]
   for block,node,kind in ((source_block,source_rr,'SOURCE'),(sink_block,sink_rr,'SINK')):
    key=rr[node];assert key[4]==kind;old=locs[block];assert key[:3]==(old[0],old[1],old[3]),'unsupported multi-tile/offset endpoint';new=moved[block];new_key=(new[0],new[1],new[3],key[3],kind);assert new_key in classes;endpoints.append(classes[new_key])
   queries.append({'net_id':net,'pin_index':pin,'source_block':source_block,'sink_block':sink_block,'source':endpoints[0],'sink':endpoints[1],'old_source':source_rr,'old_sink':sink_rr})
  assert len(queries)==sum(r[0] in dirty for r in pins);assert len({(q['net_id'],q['pin_index']) for q in queries})==len(queries);assert {q['net_id'] for q in queries}==dirty;moves.append({'pair_index':move['pair_index'],'pair':move['pair'],'queries':queries,'net_sink_counts':dict(Counter(q['net_id'] for q in queries))})
 file=out/f'{design}_{step}.json';file.write_text(json.dumps({'design':design,'epoch':released['epoch'],'step':step,'moves':moves,'inputs_sha256':{str(f):sha(f) for f in (p,context_path,table,place,graph)},'scope':'All routable native pin connections of all dirty NETs; same-site-type CLB coordinate swaps only, multi-tile offsets unsupported, root clock metadata outside contract.'},indent=2)+'\n');summaries.append({'design':design,'step':step,'moves':len(moves),'queries':sum(len(m['queries']) for m in moves),'sha256':sha(file)})
(out/'receipt.json').write_text(json.dumps({'frames':summaries,'moves':sum(x['moves'] for x in summaries),'queries':sum(x['queries'] for x in summaries),'source_sha256':sha(Path(__file__))},indent=2)+'\n');print('complete cohorts',sum(x['moves'] for x in summaries),'queries',sum(x['queries'] for x in summaries))
