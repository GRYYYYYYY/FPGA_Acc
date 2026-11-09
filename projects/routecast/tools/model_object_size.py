"""Deduplicated reachable Python object size, not allocation/RSS/peak memory."""
import sys
from collections.abc import Mapping

def children(obj):
 if isinstance(obj,Mapping):
  for k,v in obj.items():yield k;yield v
 elif isinstance(obj,(tuple,list,set,frozenset)):
  yield from obj
 elif hasattr(obj,'__dict__'):
  yield vars(obj)

def visit(root,seen):
 total=0;stack=[root]
 while stack:
  obj=stack.pop();ident=id(obj)
  if ident in seen:continue
  seen.add(ident);total+=sys.getsizeof(obj);stack.extend(children(obj))
 return total

def reachable_size(root,exclude=()):
 seen=set()
 for external in exclude:visit(external,seen)
 return visit(root,seen)
