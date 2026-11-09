"""Original/cached output, invalid path, immutable state, and digest contracts."""
import json,tempfile
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit as original
from stream_native_route_audit_cached import audit
from native_route_audit_cache import snapshot,clear_cache,STATS
xml='<rr_graph><rr_nodes><node id="0" type="SOURCE" capacity="1"/><node id="1" type="CHANX" capacity="1"/><node id="2" type="SINK" capacity="1"/></rr_nodes><switches><switch id="0"/><switch id="1"/></switches><rr_edges><edge src_node="0" sink_node="1" switch_id="0"/><edge src_node="1" sink_node="2" switch_id="1"/></rr_edges></rr_graph>'
route='Net 0 (n)\nNode: 0 SOURCE Switch: 0\nNode: 1 CHANX Switch: 1\nNode: 2 SINK Switch: -1\n'
with tempfile.TemporaryDirectory(prefix='routecast_audit_') as td:
 g=Path(td)/'graph.xml';r=Path(td)/'design.route';g.write_text(xml);r.write_text(route);clear_cache();assert original(g,r)==audit(g,r)==audit(g,r);assert STATS==dict(builds=1,hits=1,evictions=0);v=snapshot(g,sha(g))
 for mapping in [v.nodes,v.arcs]:
  try:mapping[next(iter(mapping))]=None
  except TypeError:pass
  else:raise AssertionError('mutable snapshot')
 digest=sha(g);g.write_text(xml+'\n')
 try:snapshot(g,digest)
 except ValueError:pass
 else:raise AssertionError('stale graph admitted')
 cases=[(xml,route.replace('2 SINK','99 SINK')),(xml,route+'Net 0 (n)\n'),(xml.replace('type="CHANX"','type="CHANY"'),route),(xml.replace('sink_node="2"','sink_node="1"'),route),(xml.replace('<switch id="1"/>',''),route),(xml.replace('id="1" type="CHANX" capacity="1"','id="1" type="CHANX" capacity="0"'),route),(xml.replace('</rr_nodes>','<node id="1" type="CHANX" capacity="1"/></rr_nodes>'),route)]
 for text,lines in cases:
  g.write_text(text);r.write_text(lines)
  for fn in [original,audit]:
   try:fn(g,r)
   except ValueError:pass
   else:raise AssertionError('invalid case accepted')
 # Unused duplicate nodes remain outside the printed-resource audit, matching original.
 g.write_text(xml.replace('</rr_nodes>','<node id="9" type="OPIN" capacity="1"/><node id="9" type="OPIN" capacity="1"/></rr_nodes>'));r.write_text(route);assert original(g,r)==audit(g,r)
 clear_cache()
 for k in range(4):g.write_text(xml+'\n'*k);assert original(g,r)==audit(g,r)
 assert STATS==dict(builds=4,hits=0,evictions=1)
p=Path(__file__).resolve().parents[1]/'experiments/native_route_audit_cache_contract_2026-10-07';p.mkdir();(p/'verification.json').write_text(json.dumps(dict(sources={str(f):sha(f) for f in [Path(__file__),Path(__file__).with_name('native_route_audit_cache.py'),Path(__file__).with_name('stream_native_route_audit_cached.py')]},invalid_cases=len(cases),stale_hash_rejected=True,immutable_maps=True,three_entry_eviction=True,scope='Small original/cached route audit output and rejection parity; unused graph duplicate semantics retained. Not native pin/closure legality or realgraph runtime proof.'),indent=2)+'\n');print('audit cache contract passed')
