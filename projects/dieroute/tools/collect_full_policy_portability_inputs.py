"""Inventory prepared full-policy files for unchanged-byte user-space relocation."""
from pathlib import Path
import json,collections,hashlib
R=Path(__file__).resolve().parents[1];BASE=R.parent.parent
O=R/'work/full_policy_portability_inventory_20261021'
ROOT=R/'work/persistent_native_full_policy_five_repeats_20261020/protocol.json'
def main():
 todo=[ROOT];seen=set();files={};dirs=set();missing=set();expected=collections.defaultdict(set)
 def add(p):
  p=Path(p)
  if not p.is_absolute():return
  try:p.relative_to(BASE)
  except ValueError:return
  if p.is_file():
   if str(p) not in seen:todo.append(p)
  elif p.is_dir():
   if str(p) in dirs:return
   dirs.add(str(p))
   # Known native readers consume sibling input files; do not copy historical output trees.
   if p!=R and p!=BASE and p!=R.parent:
    for x in p.iterdir():
     if x.is_file():add(x)
   if p.name=='source':
    for x in p.rglob('*'):
     if x.is_file():add(x)
   binary=p/'build/vpr/vpr'
   if binary.is_file():add(binary)
  else:
   siblings=list(p.parent.glob(p.name+'.*')) if p.parent.is_dir() else []
   found=[x for x in siblings if x.is_file()]
   if found:
    for x in found:add(x)
   else:missing.add(str(p))
 while todo:
  p=todo.pop();name=str(p)
  if name in seen:continue
  seen.add(name);st=p.stat();files[name]={'bytes':st.st_size,'symlink':p.is_symlink(),'resolved':str(p.resolve())}
  if p.suffix!='.json':continue
  try:d=json.loads(p.read_text())
  except (ValueError,UnicodeError):continue
  def walk(v,key=''):
   if isinstance(v,dict):
    for k,x in v.items():
     if k=='source_sha256' and isinstance(x,dict):
      for path,digest in x.items():
       if str(path).startswith(str(BASE)):expected[path].add(digest);add(path)
     walk(x,k)
   elif isinstance(v,list):
    for x in v:walk(x,key)
   elif isinstance(v,str) and v.startswith(str(BASE)):
    add(v)
  walk(d)
 for project in [R,R.parent/'persistroute']:
  for folder in ['tools','src','include','tb','host']:
   p=project/folder
   if p.is_dir():
    for x in p.rglob('*'):
     if x.is_file() and '__pycache__' not in x.parts:files.setdefault(str(x),{'bytes':x.stat().st_size,'symlink':x.is_symlink(),'resolved':str(x.resolve())})
  for name in ['CMakeLists.txt','README.md']:
   if (project/name).is_file():x=project/name;files.setdefault(str(x),{'bytes':x.stat().st_size,'symlink':False,'resolved':str(x)})
 d={'status':'static_full_policy_inventory_requires_runtime_validation','root_protocol':str(ROOT),'virtual_base':str(BASE),'files':files,'unique_files':len(files),'total_bytes':sum(v['bytes'] for v in files.values()),'referenced_directories':sorted(dirs),'missing_or_output_paths':sorted(missing),'conflicting_expected_hashes':{k:sorted(v) for k,v in expected.items() if len(v)>1},'scope':'Prepared complete same-input CPU policy dependency candidates,including import code and native case siblings. Static inventory doesnotprove runtime completeness or portability. No frozen input changed.','research_complete':False}
 with (O/'inventory.json').open('x') as f:json.dump(d,f,indent=2);f.write('\n')
 print(json.dumps({k:d[k] for k in ['unique_files','total_bytes','conflicting_expected_hashes']}));print('missing_or_output_paths',len(missing))
if __name__=='__main__':main()
