"""Pinned external RTL closure plus bounded pre-acquisition exposure snapshot.

No absence-to-unseen upgrade; all writes remain in this isolated experiment.
"""
import datetime,hashlib,json,re,subprocess,urllib.request
from collections import defaultdict
from pathlib import Path,PurePosixPath

R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fetch(url):
 request=urllib.request.Request(url,headers={'User-Agent':'RouteCast-source-provenance-audit','Accept':'application/vnd.github+json' if 'api.github.com' in url else '*/*'})
 with urllib.request.urlopen(request,timeout=40) as response:return response.read()
def save(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('xb') as f:f.write(data)

def main():
 out=R/'experiments/prospective_external_family_source_v1_2026-10-18';out.mkdir(exist_ok=False)
 aliases=['chacha','xchacha','salsa','salsa20','poly1305','blabla'];pattern=re.compile('|'.join(aliases),re.I)
 excludes=['-g','!**/.git/**','-g','!**/node_modules/**','-g','!projects/tileplace/work/full_color_trial_volatile_address_stage_2026-10-04/**']
 # Enumerate filenames only; do not open native routes, labels, traces or live work.
 names=[];total_files=0
 with subprocess.Popen(['rg','--files','--hidden','--no-ignore',*excludes,'projects'],cwd=REPO,stdout=subprocess.PIPE,text=True) as process:
  for name in process.stdout:
   total_files+=1
   if pattern.search(name):names.append(name.rstrip())
  assert process.wait()==0
 globs=['protocol.json','*input*capture*.json','*cases*.json','*source*inventory*.json','*source*declaration*.json','*manifest*.json']
 cmd=['rg','--files','--hidden','--no-ignore',*excludes]
 for glob in globs:cmd+=['-g',glob]
 cmd+=['projects'];paths=sorted(set(subprocess.check_output(cmd,cwd=REPO,text=True).splitlines()));hashes={};metadata_hits=[];unresolved=[];hash_locations=defaultdict(set)
 for name in paths:
  path=REPO/name
  try:
   before=path.stat();data=path.read_bytes();digest=hashlib.sha256(data).hexdigest();hashes[name]=digest
   if before.st_size>2**21:unresolved.append(dict(path=name,reason='above2MiB_text_scan_bound',bytes=before.st_size));continue
   matches=sorted(set(x.lower() for x in pattern.findall(data.decode('utf-8','replace'))))
   if matches:metadata_hits.append(dict(path=name,sha256=digest,aliases=matches))
   for h in re.findall(rb'(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])',data):hash_locations[h.decode()].add(name)
   if sha(path)!=digest:unresolved.append(dict(path=name,reason='changed_during_read'))
  except (FileNotFoundError,PermissionError,OSError) as error:unresolved.append(dict(path=name,reason=type(error).__name__))
 snapshot=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Pre-acquisition filename enumeration and bounded selected protocol/input-capture/cases/source-inventory/declaration/manifest text only across local projects. No route/trace/output-label files read. Root/outside-workspace archives and unlisted metadata/history remain gaps.',filename_count=total_files,filename_alias_hits=names,metadata_count=len(paths),metadata_sha256=hashes,metadata_alias_hits=metadata_hits,unresolved=unresolved,strict_unseen_certified=False)
 save(out/'pre_acquisition_exposure_snapshot.json',(json.dumps(snapshot,indent=2)+'\n').encode());print('PRE-ACQUISITION SNAPSHOT',len(paths),'metadata files; alias hints',len(names),len(metadata_hits),'gaps',len(unresolved),flush=True)
 api='https://api.github.com/repos/secworks/chacha';commit_raw=fetch(api+'/commits/master');commit=json.loads(commit_raw);revision=commit['sha'];tree_sha=commit['commit']['tree']['sha'];assert re.fullmatch('[0-9a-f]{40}',revision);save(out/'upstream_commit.json',commit_raw)
 tree_raw=fetch(api+'/git/trees/'+revision+'?recursive=1');tree=json.loads(tree_raw);assert not tree['truncated'] and tree['sha']==tree_sha;save(out/'upstream_tree.json',tree_raw);entries={r['path']:r for r in tree['tree'] if r['type']=='blob'}
 selected=sorted(p for p in entries if p in ['LICENSE','README.md','chacha.core'] or p.startswith('src/rtl/') or p.startswith('src/tb/'))
 assert all(p in selected for p in ['src/rtl/chacha.v','src/rtl/chacha_core.v','src/rtl/chacha_qr.v','LICENSE','README.md','chacha.core'])
 protocol=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),repository='https://github.com/secworks/chacha',resolved_ref='master',pinned_commit=revision,tree_sha1=tree_sha,selection='Independent source candidate based on explicit small Verilog RTL fileset and permissive upstream package; no synthesis/placement/route outcomes used.',selected_paths=selected,conservative_aliases=aliases,lineage_notes='ChaCha/Salsa-related derivatives, xchacha, secworks blabla and ChaCha20-Poly1305 wrappers remain conservatively linked for exposure screening. Not all ARX cryptographic designs are proven independent by this note.',prior_snapshot_sha256=sha(out/'pre_acquisition_exposure_snapshot.json'),next='Check compilation closure, explicit includes and read-only hierarchy elaboration; strict admission remains pending history/lineage audit and external exposure clarification. No new placement/native labels.',scope='Candidate acquisition, never automatic heldout certification.')
 save(out/'protocol.json',(json.dumps(protocol,indent=2)+'\n').encode());assets=[]
 for name in selected:
  p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts
  data=fetch('https://raw.githubusercontent.com/secworks/chacha/'+revision+'/'+name);entry=entries[name];assert len(data)==entry['size'];blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\x00'+data).hexdigest();assert blob==entry['sha'];target=out/'upstream'/name;save(target,data)
  assets.append(dict(path=str(target),relative=name,bytes=len(data),sha256=sha(target),upstream_git_blob_sha1=blob,official_tree_equal=True))
 rtl=[a for a in assets if a['relative'].startswith('src/rtl/') and a['relative'].endswith(('.v','.sv'))];assert len(rtl)==3;modules={};includes=[]
 for asset in rtl:
  text=Path(asset['path']).read_text();modules[asset['relative']]=re.findall(r'(?m)^\s*module\s+(\w+)',text);includes+=re.findall(r'(?m)^\s*`include\s+(.+)$',text)
 assert not includes and sorted(n for ns in modules.values() for n in ns)==['chacha','chacha_core','chacha_qr']
 core=(out/'upstream/chacha.core').read_text();assert 'license: BSD-2-Clause' in core and all(a['relative'] in core for a in rtl)
 exact_matches={a['relative']:sorted(hash_locations.get(a['sha256'],())) for a in rtl};drift=[name for name,h in hashes.items() if not (REPO/name).exists() or sha(REPO/name)!=h]
 yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';assert yosys.is_file();script='read_verilog '+' '.join('"'+a['path']+'"' for a in rtl)+'\nhierarchy -check -top chacha\nstat\n';save(out/'closure_check.ys',script.encode())
 with (out/'closure_check.log').open('x') as log:code=subprocess.call([str(yosys),'-Q','-T','-s',str(out/'closure_check.ys')],cwd=out,stdout=log,stderr=subprocess.STDOUT)
 result=dict(status='pinned_source_and_hierarchy_checked_strict_family_admission_pending' if code==0 else 'pinned_source_hierarchy_failed',repository=protocol['repository'],pinned_commit=revision,assets=assets,RTL_compilation_units=[a['relative'] for a in rtl],module_definitions=modules,explicit_include_directives=includes,hierarchy_exit_status=code,yosys_sha256=sha(yosys),prior_exact_RTL_hash_references=exact_matches,pre_acquisition_filename_alias_hits=names,pre_acquisition_metadata_alias_hits=metadata_hits,metadata_snapshot_drift=drift,metadata_unresolved=len(unresolved),strict_unseen_families_certified=0,external_history_attestation='pending_user_optional_response',new_native_labels_read=False,new_synthesis_placement_route_jobs=False,scope='Upstream commit/tree and every selected blob authenticated; explicit three-module no-include closure plus read-only Verilog frontend hierarchy check. No RTL content modifications, technology synthesis, placement, routing, target label or performance-based selection. Metadata absence cannot certify global history or independent family lineage.',bindings={str(p):sha(p) for p in [Path(__file__),out/'protocol.json',out/'pre_acquisition_exposure_snapshot.json',out/'upstream_commit.json',out/'upstream_tree.json',out/'closure_check.ys',out/'closure_check.log']})
 save(out/'source_verification.json',(json.dumps(result,indent=2)+'\n').encode());print('PINNED SOURCE CANDIDATE',revision,'assets',len(assets),'hierarchy_exit',code,'strict_unseen',0,flush=True)
 if code:raise SystemExit(code)
if __name__=='__main__':main()
