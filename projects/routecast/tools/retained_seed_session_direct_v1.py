"""Reuse original native trace templates; fresh complete retention per target."""
import re,json
from collections import defaultdict,Counter
from pathlib import Path
from retained_route_session_direct_v1 import RetainedRouteSession
from native_route_ledger_import_compact import physical_paths
from audit_native_route import NET,NODE
from pre_route_endpoints import sha

class RetainedSeedSession(RetainedRouteSession):
 def __init__(self,*args):
  super().__init__(*args)
  text=self.route.read_text();self.paths=physical_paths(self.route)
  self.pins={};self.templates=defaultdict(dict);self.headers={};self.head=[]
  keys={(self.old['net_names'][str(q['net_id'])],q['source'],q['sink']):cid for cid,q in self._queries.items()}
  if len(keys)!=len(self._queries):raise ValueError('Ambiguous original sink identity')
  name=source=None
  for line in text.splitlines():
   net=NET.match(line)
   if net:name=net[2];source=None;self.headers[name]=line;continue
   node=NODE.match(line)
   if node:
    n=int(node[1]);base=re.sub(r'Switch:\s*-?\d+','Switch: @SW@',line)
    if n in self.templates[name] and self.templates[name][n]!=base:raise ValueError('Inconsistent trace template')
    self.templates[name][n]=base
    if node[2]=='SOURCE':
     if source is not None:raise ValueError('Multiple original sources')
     source=n
    if node[2]=='SINK':
     cid=keys[name,source,n];pin=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1])
     if pin<=0 or cid in self.pins:raise ValueError('Invalid original sink pin')
     self.pins[cid]=(name,pin)
   elif name is None:self.head.append(line)
  if set(self.pins)!=set(self._queries):raise ValueError('Incomplete original sink identities')
  self._authenticate()
 def write_seed(self,target_endpoint,budget_path,directory):
  forest=self.select(target_endpoint,budget_path);target=json.loads(Path(target_endpoint).read_text())
  selected=defaultdict(list);expected={}
  for q in forest['retained']:
   name,pin=self.pins[q['connection_id']]
   paths=[p for p in self.paths[name] if (p[0][0],p[-1][0])==(q['source'],q['sink'])]
   if len(paths)!=1:raise ValueError('Ambiguous retained original branch')
   selected[name].append(paths[0]);expected[name,q['sink']]=pin
  lines=self.head[:];lines[0]='Placement_File: design.place Placement_ID: SHA256:'+target['inputs']['place']['sha256']
  for name,branches in selected.items():
   children=defaultdict(dict);parents={};roots={p[0][0] for p in branches}
   if len(roots)!=1:raise ValueError('Invalid retained root')
   for path in branches:
    for (u,_),(v,switch) in zip(path,path[1:]):
     if v in parents and parents[v]!=(u,switch):raise ValueError('Retained parent conflict')
     parents[v]=(u,switch);children[u][v]=switch
   lines.extend([self.headers[name],''])
   def emit(u):
    if not children[u]:
     line=self.templates[name][u].replace('@SW@','-1')
     if int(re.search(r'Net_pin_index:\s*(\d+)',line)[1])!=expected[name,u]:raise ValueError('Sink pin mismatch')
     lines.append(line);return
    for v,switch in children[u].items():lines.append(self.templates[name][u].replace('@SW@',str(switch)));emit(v)
   emit(next(iter(roots)));lines.append('')
  self._authenticate()
  if not all(sha(p)==h for p,h in forest['bindings'].items()):raise ValueError('Target changed during seed serialization')
  d=Path(directory);d.mkdir(exist_ok=False);out=d/'seed.route';out.write_text('\n'.join(lines)+'\n')
  actual=physical_paths(out)
  if {n:Counter(p) for n,p in actual.items()}!={n:Counter(p) for n,p in selected.items()}:raise ValueError('Serialized path mismatch')
  (d/'forest.json').write_text(json.dumps(forest,indent=2)+'\n')
  return dict(forest=forest,route=str(out),route_sha256=sha(out),retained_nets=len(selected))
