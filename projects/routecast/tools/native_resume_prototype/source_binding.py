"""Transitive local Python sources across sibling modules and root tools."""
import ast
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2]
def closure(seeds):
 result={};todo=list(seeds)
 while todo:
  path=Path(todo.pop()).resolve()
  if str(path) in result:continue
  result[str(path)]=sha(path)
  for node in ast.walk(ast.parse(path.read_text())):
   names=[node.module] if isinstance(node,ast.ImportFrom) and node.level==0 else [a.name for a in node.names] if isinstance(node,ast.Import) else []
   for name in names:
    if not name:continue
    for folder in (path.parent,ROOT/'tools'):
     module=folder/(name.split('.')[0]+'.py')
     if module.exists():todo.append(module);break
 return result
