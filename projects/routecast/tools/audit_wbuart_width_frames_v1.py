"""Independent graph and native terminal/full/dense-CID partition revalidation."""
import hashlib,json,shlex,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_width_frames_v2_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 v=json.loads((D/'verification.json').read_text());assert len(v['rows'])==12
 for n,h in v['bindings'].items():assert sha(Path(n))==h
 proto=json.loads((D/'protocol.json').read_text())
 for n,h in proto['bindings'].items():assert sha(Path(n))==h
 rows=[];graphs={}
 for w in [96,128,160]:
  graph=D/f'w{w:03d}/source/rr_graph.xml';nodekinds={};nodes=0;edges=0;switches=set();pending_edges=[]
  # Streaming schema check independent of producer graph_domain/physical_maps.
  for event,e in ET.iterparse(graph,events=['end']):
   if e.tag=='node' and 'capacity' in e.attrib:
    nid=int(e.get('id'));assert nid==nodes and int(e.get('capacity'))>0;nodes+=1
    if e.get('type') in ['SOURCE','SINK']:nodekinds[nid]=e.get('type')
    e.clear()
   elif e.tag=='switch' and 'type' in e.attrib:switches.add(int(e.get('id')));e.clear()
   elif e.tag=='edge':
    a,b,s=map(int,[e.get('src_node'),e.get('sink_node'),e.get('switch_id')]);assert 0<=a<nodes and 0<=b<nodes and s in switches;edges+=1;e.clear()
  ghash=sha(graph);assert (nodes,edges,ghash)==tuple(v['graphs'][str(w)][k] for k in ['nodes','edges','graph_sha256']);graphs[str(w)]={'nodes':nodes,'edges':edges,'sha256':ghash};source=None
  for name in ['source','episode_01','episode_02','episode_03']:
   p=D/f'w{w:03d}'/name;fv=json.loads((p/'verification.json').read_text())
   for n,h in fv['bindings'].items():assert sha(Path(n))==h
   full=json.loads((p/'endpoints.json').read_text());route=json.loads((p/'routing_endpoints.json').read_text());partition=json.loads((p/'native_ignored_partition.json').read_text());names={int(i):n for i,n in full['net_names'].items()};native={};header=None
   for line in (p/'native_terminals.txt').read_text().splitlines():
    t=shlex.split(line)
    if not t:continue
    if t[0]=='H':assert header is None;header=list(map(int,t[1:]));continue
    assert t[0]=='N' and t[2] not in native;native[t[2]]={'ignored':int(t[3]),'global':int(t[4]),'clock':int(t[5]),'terms':list(map(int,t[7:]))};assert len(native[t[2]]['terms'])==int(t[6])
   assert header==[nodes,edges,len(native)] and set(native)==set(names.values());assert {n for n,x in native.items() if x['clock']}=={'i_clk'};assert {n for n,x in native.items() if x['ignored'] and not x['clock']}=={'o_wb_stall','o_wb_data[31]'}
   declared=Counter();routed=Counter()
   for n,x in native.items():
    t=x['terms'];assert nodekinds[t[0]]=='SOURCE' and all(nodekinds[s]=='SINK' for s in t[1:])
    if x['clock']:continue
    declared.update((n,t[0],s) for s in t[1:])
    if not x['ignored']:routed.update((n,t[0],s) for s in t[1:])
   counter=lambda e:Counter((names[q['net_id']],q['source'],q['sink']) for q in e['connections'])
   assert counter(full)==declared and counter(route)==routed and len(full['connections'])==2495 and len(route['connections'])==2493
   old={q['connection_id']:q for q in full['connections']};assert list(old)==list(range(2495));seen=set()
   for i,q in enumerate(route['connections']):
    assert q['connection_id']==i and q['full_connection_id'] not in seen;seen.add(q['full_connection_id']);o=old[q['full_connection_id']];assert all(q[k]==o[k] for k in ['net_id','source','sink']) and not native[names[q['net_id']]]['ignored']
   omitted=set(old)-seen;assert len(omitted)==2 and {q['connection_id'] for q in partition['omitted_connections']}==omitted
   for n,x in native.items():assert partition['flags'][n]=={k:x[k] for k in ['ignored','global']}
   assert all(full['graph_sha256']==route['graph_sha256']==fv['graph_sha256']==ghash for _ in [0]);assert not list(p.glob('*.route'))
   if source is None:source=route;changed=0
   else:
    assert route['net_names']==source['net_names'];a={q['connection_id']:q for q in source['connections']};assert all(q['net_id']==a[q['connection_id']]['net_id'] and q['full_connection_id']==a[q['connection_id']]['full_connection_id'] for q in route['connections']);changed=sum((q['source'],q['sink'])!=(a[q['connection_id']]['source'],a[q['connection_id']]['sink']) for q in route['connections'])
   assert changed=={'source':0,'episode_01':94,'episode_02':17,'episode_03':62}[name];rows.append({'width':w,'frame':name,'declared_connections':2495,'routing_connections':2493,'affected_connections':changed})
 assert len({g['sha256'] for g in graphs.values()})==3
 out={'status':'ALL12_NATIVE_GRAPH_TERMINAL_MULTISETS_AND_COMPLETE_CID_PARTITIONS_INDEPENDENTLY_VERIFIED','rows':rows,'graphs':graphs,'strict_unseen_admitted':False,'new_route_labels':False,'bindings':{str(p):sha(p) for p in [Path(__file__),D/'verification.json',D/'protocol.json']}}
 (D/'independent_verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
