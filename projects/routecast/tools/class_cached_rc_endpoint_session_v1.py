"""Single-process authenticated RR template cache with isolated mutable CSR copies."""
import json
from array import array
from pathlib import Path
from collections import OrderedDict
from class_cached_rc_endpoint_context_v1 import load_endpoints as build
from class_cached_integer_rc_v1 import IntegerRC
from csr_exact_buffered_rc import ExactBufferedRC
from cached_rr_endpoint_context_classes import freeze_node
from pre_route_endpoints import sha
_CACHE=OrderedDict();STATS=dict(builds=0,hits=0,evictions=0)
def clear_cache():
 _CACHE.clear()
 for k in STATS:STATS[k]=0

def load_endpoints(endpoint_path):
 ep=json.loads(Path(endpoint_path).read_text())
 if not all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values()):raise ValueError('Changed endpoint input')
 graph=Path(ep['inputs']['graph']['path']);digest=sha(graph)
 if digest!=ep['graph_sha256']:raise ValueError('Changed graph hash')
 version=tuple(sha(Path(__file__).with_name(name)) for name in ('class_cached_rc_endpoint_session_v1.py','class_cached_rc_endpoint_context_v1.py','class_cached_integer_rc_v1.py','csr_exact_buffered_rc.py','path_rc.py'))
 key=(str(graph.resolve()),digest,version)
 if key not in _CACHE:
  _,actual,nodes,f,rc,_=build(endpoint_path)
  if actual!=digest or sha(graph)!=digest:raise ValueError('Graph changed during build')
  snapshot=dict(nodes=tuple(freeze_node(n) for n in nodes),fields={k:a.tobytes() for k,a in f.items()},node_classes=rc.rc.node_classes.tobytes(),classes=tuple(rc.rc.classes),switches=dict(rc.rc.switches),increments=tuple(rc.increments),scale=rc.scale,initial_by_class=dict(rc.initial_by_class),arc_cache=dict(rc.rc.cache))
  _CACHE[key]=snapshot;STATS['builds']+=1
  if len(_CACHE)>3:_CACHE.popitem(last=False);STATS['evictions']+=1
 else:STATS['hits']+=1
 _CACHE.move_to_end(key);s=_CACHE[key]
 def copy(data):
  a=array('Q');a.frombytes(data);return a
 fields={k:copy(data) for k,data in s['fields'].items()}
 electrical=ExactBufferedRC(fields,copy(s['node_classes']),s['classes'],dict(s['switches']));electrical.cache=dict(s['arc_cache'])
 integer=object.__new__(IntegerRC);integer.rc=electrical;integer.fields=fields;integer.scale=s['scale'];integer.increments=list(s['increments']);integer.initial_by_class=dict(s['initial_by_class'])
 return graph,digest,s['nodes'],fields,integer,ep['connections']
