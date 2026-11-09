"""Revalidate source provenance and bounded local RTL exposure, never unseen proof."""
import datetime,hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]; REPO=R.parents[1]
S=R/'experiments/wbuart_source_candidate_v2_2026-10-20'
O=R/'experiments/wbuart_source_lineage_v1_2026-10-20'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(n,d):
 with (O/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
 O.mkdir(exist_ok=False)
 commit=json.loads((S/'commit.json').read_text());tree=json.loads((S/'tree.json').read_text());assert tree['sha']==commit['commit']['tree']['sha'] and not tree['truncated']
 entries={e['path']:e for e in tree['tree'] if e['type']=='blob'}
 declared=['rxuartlite.v','txuartlite.v','rxuart.v','txuart.v','ufifo.v','wbuart.v']
 core=(S/'upstream/wbuart32.core').read_text();section=core.split('[fileset rtl]')[1].split('file_type')[0];actual=re.findall(r'rtl/([^\s]+\.v)',section);assert actual==declared
 assets=[];digests={};modules=set()
 for p in sorted((S/'upstream').rglob('*')):
  if not p.is_file():continue
  n=str(p.relative_to(S/'upstream'));b=p.read_bytes();e=entries[n];assert e['size']==len(b) and e['sha']==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
  assets.append({'path':n,'sha256':sha(b),'git_blob':e['sha']})
  if n in ['rtl/'+x for x in declared]:
   digests[sha(b)]=n;modules.update(re.findall(rb'(?m)^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)',b))
 license_text=(S/'upstream/LICENSE').read_text();assert 'GNU GENERAL PUBLIC LICENSE' in license_text and 'Version 3' in license_text
 cmd=['rg','--files','--hidden','--no-ignore','-g','!**/.git/**','-g','!**/node_modules/**','-g','!projects/tileplace/work/full_color_trial_volatile_address_stage_2026-10-04/**','-g','*.v','-g','*.sv','-g','*.vh','projects']
 protocol={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'max_file_bytes':2**21,'modules':sorted(m.decode() for m in modules),'aliases':['wbuart','zipcpu','gisselquist'],'scope':'RTL text only, no route/trace/label files; exact whole-file hashes, module declarations and author/project aliases are hints, not equivalence or independent-family certification.','introduced_prefix':'projects/routecast/experiments/wbuart_source_candidate_','strict_unseen_certified':False}
 save('protocol.json',protocol)
 names=sorted(set(subprocess.check_output(cmd,cwd=REPO,text=True).splitlines()));hits=[];gaps=[];snapshot={};total=0
 for n in names:
  p=REPO/n
  try:
   st=p.stat()
   if st.st_size>2**21:gaps.append({'path':n,'reason':'above_2MiB_bound','bytes':st.st_size});continue
   b=p.read_bytes();after=p.stat()
   if (st.st_size,st.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):gaps.append({'path':n,'reason':'changed_during_read'});continue
   h=sha(b);snapshot[n]={'sha256':h,'bytes':len(b)};total+=len(b)
   ms=sorted(m.decode() for m in set(re.findall(rb'(?m)^\s*module\s+([A-Za-z_][A-Za-z0-9_$]*)',b))&modules)
   aliases=[a for a in protocol['aliases'] if a.encode() in b.lower()]
   if ms or aliases or h in digests:hits.append({'path':n,'sha256':h,'module_name_overlap':ms,'aliases':aliases,'exact_rtl':digests.get(h),'introduced':n.startswith(protocol['introduced_prefix'])})
  except OSError as e:gaps.append({'path':n,'reason':type(e).__name__})
 prior=[h for h in hits if not h['introduced']]
 save('verification.json',{'status':'PINNED_BLOBS_AND_DECLARED_FILESET_REVALIDATED_BOUNDED_RTL_EXPOSURE_SCANNED','commit':commit['sha'],'tree':tree['sha'],'assets':assets,'declared_rtl_files':declared,'license':'GPL-3.0-or-later per RTL headers; upstream GPLv3 LICENSE retained','filename_count':len(names),'scanned_files':len(snapshot),'scanned_bytes':total,'hits':hits,'prior_hint_count':len(prior),'gaps':gaps,'snapshot':snapshot,'strict_unseen_families_certified':0,'new_target_labels_read':False,'limitations':['Archive payloads and non-RTL metadata not scanned here.','Modified lineage, aliases and outside-workspace history remain unresolved.','Source author overlap alone is not shared implementation or label exposure.'],'bindings':{'tool':sha(Path(__file__).read_bytes()),'protocol':sha((O/'protocol.json').read_bytes()),'source_hierarchy_proof':sha((S/'hierarchy_fileset_verification_v1.json').read_bytes())}})
 print(json.dumps({'files':len(snapshot),'prior_hints':len(prior),'gaps':len(gaps),'bytes':total}))
if __name__=='__main__':main()
