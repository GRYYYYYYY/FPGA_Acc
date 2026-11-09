"""Pinned official source acquisition only, with pre-acquisition local evidence."""
import json,hashlib,re,urllib.request,time
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_candidate_source_v2_2026-10-20'
def digest(b):return hashlib.sha256(b).hexdigest()
def fetch(url):
 request=urllib.request.Request(url,headers={'User-Agent':'RouteCast-source-provenance-audit'})
 with urllib.request.urlopen(request,timeout=40) as response:return response.read()
def save(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.open('xb').write(b)
def main():
 D.mkdir(exist_ok=False);screen=E/'local_family_metadata_screen_v1_2026-10-20/verification.json';s=json.loads(screen.read_text());matches=[];drift=[];pattern=re.compile(r'\bprince(?:_core)?\b',re.I)
 for row in s['metadata']:
  p=R/row['path'];b=p.read_bytes()
  if digest(b)!=row['sha256']:drift.append(row['path']);continue
  if pattern.search(b.decode('utf-8','replace')):matches.append({'path':str(p),'sha256':digest(b)})
 snapshot=json.loads((E/'prince_candidate_source_v1_2026-10-20/pre_acquisition_snapshot.json').read_text());save(D/'pre_acquisition_snapshot.json',(json.dumps(snapshot,indent=2)+'\n').encode())
 api='https://api.github.com/repos/secworks/prince';repo=fetch(api);save(D/'official_repository.json',repo);branch=json.loads(repo)['default_branch'];raw=(E/'prince_candidate_source_v1_2026-10-20/official_commit.json').read_bytes();save(D/'official_commit.json',raw);commit=json.loads(raw);revision=commit['sha'];tree_raw=fetch(api+'/git/trees/'+commit['commit']['tree']['sha']+'?recursive=1');save(D/'official_tree.json',tree_raw);tree=json.loads(tree_raw);assert not tree['truncated'] and tree['sha']==commit['commit']['tree']['sha'];entries={x['path']:x for x in tree['tree'] if x['type']=='blob'};selected=sorted(name for name in entries if name in ['LICENSE','README.md','prince.core'] or name.startswith('src/rtl/'));assert 'LICENSE' in selected and 'README.md' in selected;assets=[]
 for name in selected:
  p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts;b=fetch('https://raw.githubusercontent.com/secworks/prince/'+revision+'/'+name);entry=entries[name];assert len(b)==entry['size'] and hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()==entry['sha'];target=D/'upstream'/name;save(target,b);assets.append({'path':str(target),'relative':name,'sha256':digest(b),'git_blob_sha1':entry['sha'],'bytes':len(b)})
 rtl=[a for a in assets if a['relative'].startswith('src/rtl/') and a['relative'].endswith(('.v','.sv'))];assert rtl;modules={};includes=[]
 for a in rtl:
  t=Path(a['path']).read_text();modules[a['relative']]=re.findall(r'(?m)^\s*module\s+(\w+)',t);includes+=re.findall(r'(?m)^\s*`include\s+(.+)$',t)
 result={'status':'PINNED_PRINCE_SOURCE_ACQUIRED_FRONTEND_AND_LINEAGE_PENDING','repository':'https://github.com/secworks/prince','revision':revision,'assets':assets,'RTL_compilation_units':[a['relative'] for a in rtl],'modules':modules,'explicit_includes':includes,'strict_unseen_admitted':False,'new_native_labels':False,'scope':'Byte-preserving source acquisition with official commit/tree/blob verification only. License archived, semantic/frontend equivalence and global lineage not yet admitted. No synth/place/route outcomes used to select candidate.','bindings':{str(p):digest(p.read_bytes()) for p in [Path(__file__),screen,E/'prince_candidate_acquisition_design_v1_2026-10-20/protocol.json',D/'pre_acquisition_snapshot.json',D/'official_repository.json',D/'official_commit.json',D/'official_tree.json']}};save(D/'verification.json',(json.dumps(result,indent=2)+'\n').encode());print('PRINCE_PINNED_SOURCE_ACQUIRED',revision,len(rtl),modules,flush=True)
if __name__=='__main__':main()
