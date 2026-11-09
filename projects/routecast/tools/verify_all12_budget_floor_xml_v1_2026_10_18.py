"""Independent XML decimal/Fraction extraction and clipped-potential proof."""
import json,hashlib,time,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
R=Path(__file__).resolve().parents[1];P=R/'experiments/all12_native_budget_floors_v1_2026-10-18';D=R/'experiments/all12_budget_floor_xml_v1_2026-10-18';D.mkdir(exist_ok=False);bindings={}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):
 p=Path(p);bindings[str(p)]=sha(p);return json.loads(p.read_text())
report=load(P/'verification.json');protocol=load(P/'protocol.json')
for p,h in report['bindings'].items():assert sha(p)==h;bindings[p]=h
rows=[];certrows=[];start=time.perf_counter()
for width in (8,16,32):
 plans=[p for p in protocol['plans'] if p['width']==width];meta=load(plans[0]['endpoint']);graph=Path(meta['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256'];bindings[str(graph)]=sha(graph)
 nodes={};switches={};edges=[];stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   nid=int(e.get('id'));assert nid not in nodes;t=e.find('timing');r=F(t.get('R'));c=F(t.get('C'));assert r>=0 and c>=0;nodes[nid]=(int(e.get('capacity')),r,c)
  elif e.tag=='switch' and parent=='switches':
   sid=int(e.get('id'));assert sid not in switches and e.get('type') in {'buffer','mux','tristate'};t=e.find('timing');assert F(t.get('Cinternal','0'))==0;sr=F(t.get('R','0'));td=F(t.get('Tdel','0'));assert sr>=0 and td>=0;switches[sid]=(sr,td)
  elif e.tag=='edge' and parent=='rr_edges':edges.append(tuple(int(e.get(k)) for k in ['src_node','sink_node','switch_id']))
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 expected_sources={p['query']['source'] for p in plans}
 certspec=[s for s in report['certificates'] if Path(s['path']).name.startswith(f'w{width}_')];seen=set()
 for spec in certspec:
  assert sha(spec['path'])==spec['sha256'];cert=load(spec['path']);source=cert['source'];assert source in expected_sources and source not in seen;seen.add(source);assert cert['graph_sha256']==meta['graph_sha256'];scale=cert['scale'];assert type(scale) is int and scale>0
  # Independent exact Fraction increments; scale only accepted if every value integral.
  if 'weights' not in locals() or cached_scale!=scale:
   weights=[];cache={}
   for u,v,s in edges:
    _,r,c=nodes[v];sr,td=switches[s];key=(r,c,sr,td)
    if key not in cache:
     value=((sr+r/2)*c+td)*scale;assert value.denominator==1;cache[key]=value.numerator
    weights.append(cache[key])
   cached_scale=scale
  clip=cert['clip'];pot={int(n):v for n,v in cert['potentials'].items()};assert all(n in nodes and nodes[n][0]>0 and type(v) is int and 0<=v<clip for n,v in pot.items())
  initial=nodes[source][1]*nodes[source][2]/2;assert nodes[source][0]>0;assert F(pot.get(source,clip),scale)<=initial
  inequalities=0
  for (u,v,s),weight in zip(edges,weights):
   if nodes[u][0]>0 and nodes[v][0]>0:assert pot.get(v,clip)<=pot.get(u,clip)+weight;inequalities+=1
  group=[p for p in plans if p['query']['source']==source];targets={p['query']['sink'] for p in group};assert {int(t) for t in cert['witnesses']}==targets
  for target in targets:
   current=source;visited={source};value=initial
   for eid in cert['witnesses'][str(target)]:
    assert type(eid) is int and 0<=eid<len(edges);u,v,s=edges[eid];assert u==current and v not in visited and nodes[v][0]>0;visited.add(v);value+=F(weights[eid],scale);current=v
   assert current==target and value==F(pot.get(target,clip),scale)
   for plan in [p for p in group if p['query']['sink']==target]:
    minimum=value*10**9;limit=F(plan['budget_ns']);classification='RELAXED_FLOOR_EXCEEDS_BUDGET' if minimum>limit else 'RELAXED_WITHIN_BUDGET_PATH_EXISTS';original=next(r for r in report['rows'] if (r['width'],r['index'],r['connection_id'])==(width,plan['index'],plan['query']['connection_id']));assert F(original['minimum_ns'])==minimum and original['classification']==classification;rows.append(dict(width=width,index=plan['index'],connection_id=plan['query']['connection_id'],classification=classification,minimum_ns=str(minimum),budget_ns=str(limit)))
  certrows.append(dict(width=width,source=source,all_edge_inequalities=inequalities))
 assert seen==expected_sources;del weights;print(width,'independent XML certificates PASS',len(seen),flush=True)
assert len(rows)==len(protocol['plans'])==81
counts=Counter(r['classification'] for r in rows);casecounts=Counter((r['width'],r['index']) for r in rows if r['classification']=='RELAXED_FLOOR_EXCEEDS_BUDGET');assert len(casecounts)==12
bindings[str(Path(__file__))]=sha(__file__);assert all(sha(p)==h for p,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,certificates=certrows,counts=dict(counts),all12_have_proven_floor_exceedance=True,verification_seconds=time.perf_counter()-start,scope='Independent original XML Fraction RC extraction; exact integral rescaling, all admissible edge inequalities and attaining physical witnesses. Proves relaxed additive RC minimum, not native shared-tree STA or physical unroutability.',decision='Close complete unchanged-original-budget acceptance for these12 fixed targets: every target has at least one physically unattainable connection budget under this additive model. Do not spend on further constrained repair claiming all-budget acceptance, or silently relax budgets.'),f,indent=2);f.write('\n')
