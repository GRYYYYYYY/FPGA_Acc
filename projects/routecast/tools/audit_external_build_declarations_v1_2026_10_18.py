"""Focused FuseSoC/Tcl/make declaration audit; vendor copies explicitly excluded."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=R/'experiments/prospective_external_family_build_declarations_v1_2026-10-18';out.mkdir(exist_ok=False);regpath=R/'experiments/prospective_external_family_admission_review_v2_2026-10-18/candidate_registry_v1.json';reg=json.loads(regpath.read_text());aliases=[a.encode() for a in reg['conservative_aliases']]
 globs=['*.core','*.tcl','*.mk','Makefile','*.lst','*.list'];cmd=['rg','--files','--hidden','--no-ignore']
 for excluded in ['!**/.git/**','!**/third_party/**','!**/build*/**','!**/node_modules/**','!**/source_vtr/**','!**/source_yosys/**','!**/source_abc/**','!projects/tileplace/work/full_color_trial_volatile_address_stage_2026-10-04/**']:cmd+=['-g',excluded]
 for glob in globs:cmd+=['-g',glob]
 names=sorted(set(subprocess.check_output(cmd+['projects'],cwd=REPO,text=True).splitlines()));snapshot={};prior=[];introduced=[];gaps=[]
 for name in names:
  p=REPO/name
  try:
   st=p.stat();h=hashlib.sha256();tail=b'';hits=set()
   with p.open('rb') as f:
    for chunk in iter(lambda:f.read(2**20),b''):
     h.update(chunk);data=(tail+chunk).lower();hits.update(a.decode() for a in aliases if a in data);tail=data[-128:]
   if (p.stat().st_size,p.stat().st_mtime_ns)!=(st.st_size,st.st_mtime_ns):gaps.append(dict(path=name,reason='changed_during_read'));continue
   snapshot[name]=dict(sha256=h.hexdigest(),bytes=st.st_size)
   if hits:
    row=dict(path=name,sha256=h.hexdigest(),aliases=sorted(hits))
    if name.startswith('projects/routecast/experiments/prospective_external_family_'):introduced.append(row)
    else:prior.append(row)
  except OSError as error:gaps.append(dict(path=name,reason=type(error).__name__))
 drift=[name for name,record in snapshot.items() if not (REPO/name).exists() or sha(REPO/name)!=record['sha256']]
 result=dict(status='focused_build_declarations_scanned_strict_admission_pending',bindings={str(regpath):sha(regpath),str(Path(__file__)):sha(__file__)},formats=globs,files=len(names),snapshot=snapshot,prior_alias_hits=prior,introduced_staging_hits=introduced,unresolved=gaps,drift=drift,strict_unseen_families_certified=0,scope='Selected live project build declarations only. Vendor copies under explicit exclusions are not independently rescanned here; prior source/filename inventory remains separate. No archive payload/native label decoding or admission by absence.')
 with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(dict(files=len(names),prior_hits=len(prior),introduced_hits=len(introduced),unresolved=len(gaps),drift=len(drift))),flush=True)
if __name__=='__main__':main()
