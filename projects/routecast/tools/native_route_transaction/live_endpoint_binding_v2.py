"""Bind prepared endpoint queries to current native identity before any search."""
import json
from pathlib import Path

def validate(endpoint,identity,inventory):
 meta=json.loads(Path(endpoint).read_text());rows=list(map(json.loads,Path(identity).read_text().splitlines()));nets={r['name']:r for r in rows}
 if len(nets)!=len(rows):raise ValueError('duplicate native NET name')
 seen=set()
 for q in meta['connections']:
  name=meta['net_names'][str(q['net_id'])]
  if name not in nets:raise ValueError('live endpoint NET name mismatch')
  pins=nets[name]['pins']
  def site(node):
   kind,loc=inventory.nodes[node]
   return kind,tuple(int(loc.get(k,'0')) for k in ('xlow','ylow','layer','ptc'))
  kind,source=site(q['source']);sinkkind,sink=site(q['sink'])
  if kind!='SOURCE' or sinkkind!='SINK':raise ValueError('live endpoint RR node kind mismatch')
  drivers=[p for p in pins if p['index']==0 and tuple(p[k] for k in ('x','y','layer','class'))==source]
  sinks=[p for p in pins if p['index']>0 and tuple(p[k] for k in ('x','y','layer','class'))==sink]
  if len(drivers)!=1 or len(sinks)!=1:raise ValueError('live endpoint site/class mismatch or ambiguity')
  key=(name,sinks[0]['index'])
  if key in seen:raise ValueError('duplicate live endpoint pin')
  seen.add(key)
 routed_names={meta['net_names'][str(q['net_id'])] for q in meta['connections']}
 expected={(name,p['index']) for name,net in nets.items() if name in routed_names for p in net['pins'] if p['index']>0}
 if seen!=expected:raise ValueError('incomplete live endpoint pin coverage')
 return len(seen)
