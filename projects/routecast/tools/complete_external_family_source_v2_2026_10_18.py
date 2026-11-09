"""Resume pinned acquisition from frozen pre-acquisition snapshot, exact tree SHA."""
import hashlib,json,re,subprocess,urllib.request
from pathlib import Path,PurePosixPath
from collections import defaultdict
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fetch(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'RouteCast-source-provenance-audit'}),timeout=40) as f:return f.read()
def save(p,data):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(data)
def main():
 prior=R/'experiments/prospective_external_family_source_v1_2026-10-18';out=R/'experiments/prospective_external_family_source_v2_2026-10-18';out.mkdir(exist_ok=False);snapshot_path=prior/'pre_acquisition_exposure_snapshot.json';snapshot=json.loads(snapshot_path.read_text());commitpath=prior/'upstream_commit.json';commit=json.loads(commitpath.read_text());revision=commit['sha'];tree_sha=commit['commit']['tree']['sha'];assert len(revision)==len(tree_sha)==40
 save(out/'pre_acquisition_exposure_snapshot.json',snapshot_path.read_bytes());save(out/'upstream_commit.json',commitpath.read_bytes())
 raw=fetch('https://api.github.com/repos/secworks/chacha/git/trees/'+tree_sha+'?recursive=1');tree=json.loads(raw);save(out/'upstream_tree.json',raw);assert tree['sha']==tree_sha and not tree['truncated'];entries={e['path']:e for e in tree['tree']};trees={'':tree_sha,**{name:e['sha'] for name,e in entries.items() if e['type']=='tree'}}
 # Recompute every tree object, including links to the downloaded leaf blobs.
 for prefix,expected in trees.items():
  children=[]
  for name,e in entries.items():
   parent=str(PurePosixPath(name).parent);parent='' if parent=='.' else parent
   if parent==prefix:children.append((PurePosixPath(name).name,e))
  content=b''
  for name,e in sorted(children,key=lambda item:(item[0]+('/' if item[1]['type']=='tree' else '')).encode()):content+=e['mode'].lstrip('0').encode()+b' '+name.encode()+b'\x00'+bytes.fromhex(e['sha'])
  assert hashlib.sha1(b'tree '+str(len(content)).encode()+b'\x00'+content).hexdigest()==expected
 selected=sorted(name for name,e in entries.items() if e['type']=='blob' and (name in ['LICENSE','README.md','chacha.core'] or name.startswith('src/rtl/') or name.startswith('src/tb/')))
 protocol=dict(repository='https://github.com/secworks/chacha',pinned_commit=revision,pinned_tree_sha1=tree_sha,prior_snapshot_sha256=sha(snapshot_path),selected_paths=selected,conservative_aliases=['chacha','xchacha','salsa','salsa20','poly1305','blabla'],eligibility='Source/closure candidate only; strict family history remains unresolved. Functional source admission before target labels; no performance-based source selection.',recovery='Earlier commit-addressed GitHub tree response echoed the commit SHA. Use exact tree SHA from pinned commit and recompute all recursive Git tree objects, preserving earlier observation.',scope='Pinned source acquisition and read-only syntax/hierarchy preflight, no technology synthesis/placement/routing.')
 save(out/'protocol.json',(json.dumps(protocol,indent=2)+'\n').encode());assets=[]
 for name in selected:
  p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts;data=fetch('https://raw.githubusercontent.com/secworks/chacha/'+revision+'/'+name);e=entries[name];assert len(data)==e['size'];blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\x00'+data).hexdigest();assert blob==e['sha'];path=out/'upstream'/name;save(path,data);assets.append(dict(relative=name,path=str(path),sha256=sha(path),bytes=len(data),upstream_git_blob_sha1=blob))
 rtl=[e for e in assets if e['relative'].startswith('src/rtl/') and e['relative'].endswith(('.v','.sv'))];assert {e['relative'] for e in rtl}=={'src/rtl/chacha.v','src/rtl/chacha_core.v','src/rtl/chacha_qr.v'}
 modules={};includes=[]
 for e in rtl:
  text=Path(e['path']).read_text();modules[e['relative']]=re.findall(r'(?m)^\s*module\s+(\w+)',text);includes+=re.findall(r'(?m)^\s*`include\s+(.+)$',text)
 assert sorted(n for ns in modules.values() for n in ns)==['chacha','chacha_core','chacha_qr'] and not includes;core=(out/'upstream/chacha.core').read_text();assert 'license: BSD-2-Clause' in core and all(e['relative'] in core for e in rtl)
 matches=defaultdict(list);drift=[]
 for name,h in snapshot['metadata_sha256'].items():
  path=REPO/name
  if not path.exists() or sha(path)!=h:drift.append(name);continue
  if path.stat().st_size>2**21:continue
  data=path.read_bytes()
  for e in rtl:
   if e['sha256'].encode() in data:matches[e['relative']].append(name)
 yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';assert yosys.is_file();script='read_verilog '+' '.join('"'+e['path']+'"' for e in rtl)+'\nhierarchy -check -top chacha\nstat\n';save(out/'closure_check.ys',script.encode())
 with (out/'closure_check.log').open('x') as log:code=subprocess.call([str(yosys),'-Q','-T','-s',str(out/'closure_check.ys')],cwd=out,stdout=log,stderr=subprocess.STDOUT)
 result=dict(status='pinned_source_and_hierarchy_verified_strict_family_admission_pending' if code==0 else 'pinned_source_hierarchy_failed',repository=protocol['repository'],pinned_commit=revision,pinned_tree_sha1=tree_sha,all_recursive_git_tree_objects_recomputed=len(trees),assets=assets,RTL_compilation_units=[e['relative'] for e in rtl],module_definitions=modules,explicit_include_directives=includes,hierarchy_exit_status=code,yosys_path=str(yosys),yosys_sha256=sha(yosys),prior_exact_RTL_hash_references={e['relative']:matches[e['relative']] for e in rtl},pre_acquisition_filename_alias_hits=snapshot['filename_alias_hits'],pre_acquisition_metadata_alias_hits=snapshot['metadata_alias_hits'],metadata_snapshot_drift=drift,metadata_unresolved=snapshot['unresolved'],strict_unseen_families_certified=0,external_history_attestation='pending_optional_user_response',new_native_labels_read=False,new_technology_synthesis_placement_route_jobs=False,scope='Exact pinned commit/tree/blob closure, three complete RTL units with no include directives, read-only frontend hierarchy check. Negative bounded metadata evidence is not global-history or independent-family certification.',bindings={str(p):sha(p) for p in [Path(__file__),snapshot_path,commitpath,out/'pre_acquisition_exposure_snapshot.json',out/'upstream_commit.json',out/'upstream_tree.json',out/'protocol.json',out/'closure_check.ys',out/'closure_check.log']})
 save(out/'source_verification.json',(json.dumps(result,indent=2)+'\n').encode());print('PINNED CANDIDATE',revision,'RTL',len(rtl),'assets',len(assets),'hierarchy exit',code,'drift',len(drift),'strict unseen',0,flush=True)
 if code:raise SystemExit(code)
if __name__=='__main__':main()
