"""Read-only declaration/script and archive-index screening, never unseen proof."""
import datetime,hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def enumerate_files(globs):
 cmd=['rg','--files','--hidden','--no-ignore','-g','!**/.git/**','-g','!**/node_modules/**','-g','!**/third_party/**','-g','!**/build*/**','-g','!**/.venv/**','-g','!**/site-packages/**','-g','!**/__pycache__/**','-g','!projects/tileplace/work/full_color_trial_volatile_address_stage_2026-10-04/**']
 for glob in globs:cmd+=['-g',glob]
 return sorted(set(subprocess.check_output(cmd+['projects'],cwd=REPO,text=True).splitlines()))
def main():
 out=R/'experiments/prospective_external_family_nonJSON_exposure_v1_2026-10-18';out.mkdir(exist_ok=False)
 registry=R/'experiments/prospective_external_family_admission_review_v2_2026-10-18/candidate_registry_v1.json';reg=json.loads(registry.read_text());proofpath=registry.with_name('verification.json');proof=json.loads(proofpath.read_text());assert proof['read_only_hierarchy_pass'] and not reg['strict_unseen_admitted']
 introduced_scripts={'prepare_external_family_candidate_v1_2026_10_18.py','complete_external_family_source_v2_2026_10_18.py','check_external_family_runtime_v1_2026_10_18.py','verify_external_family_candidate_v1_2026_10_18.py','verify_external_family_candidate_v2_2026_10_18.py',Path(__file__).name}
 def introduced(name):return name.startswith('projects/routecast/experiments/prospective_external_family_') or name.startswith('projects/routecast/tools/') and Path(name).name in introduced_scripts
 globs=['*.yaml','*.yml','*.toml','*.ini','*.cfg','*.f','*.ys','config.txt','*manifest*.txt','*source*list*.txt','*.sh','*.py']
 paths=enumerate_files(globs);archives=enumerate_files(['*.zip','*.tar','*.tar.gz','*.tgz','*.tar.xz','*.tar.zst','*.7z']);aliases=reg['conservative_aliases'];pattern=re.compile(b'|'.join(a.encode() for a in aliases),re.I);source=R/'experiments/prospective_external_family_source_v2_2026-10-18/source_verification.json';sv=json.loads(source.read_text());digests={a['relative']:a['sha256'].encode() for a in sv['assets'] if a['relative'] in reg['RTL_compilation_units']};snapshot={};hits=[];gaps=[];introduced_records=[]
 protocol=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),bindings={str(p):sha(p) for p in [registry,proofpath,source,Path(__file__)]},declaration_globs=globs,excluded='Third_party/build/dependency caches and protected TilePlace experiment. Route/trace/label output formats are not parsed.',introduced_staging_rule='Candidate staging directories and explicitly listed preparation/check scripts are recorded but cannot be counted as prior exposure.',introduced_scripts=sorted(introduced_scripts),aliases=aliases,archive_scope='Enumerate archive filenames and sizes, scan selected source/manifest indices only. Do not decode archive payloads or classify unnamed payloads as clean.',scope='Additional bounded local evidence, not global/modified-lineage proof and not automatic strict-family admission.')
 with (out/'protocol.json').open('x') as f:json.dump(protocol,f,indent=2)
 for name in paths:
  p=REPO/name
  try:
   before=p.stat();h=hashlib.sha256();tail=b'';found=set();exact=set()
   with p.open('rb') as f:
    for chunk in iter(lambda:f.read(2**20),b''):
     h.update(chunk);data=tail+chunk;found.update(x.decode().lower() for x in pattern.findall(data))
     for rtl,digest in digests.items():
      if digest in data:exact.add(rtl)
     tail=data[-128:]
   digest=h.hexdigest();after=p.stat()
   if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):gaps.append(dict(path=name,reason='changed_during_read'));continue
   snapshot[name]=dict(sha256=digest,bytes=before.st_size)
   record=dict(path=name,sha256=digest,aliases=sorted(found),exact_RTL_hashes=sorted(exact))
   if introduced(name):introduced_records.append(record)
   elif found or exact:hits.append(record)
  except (OSError,UnicodeError) as e:gaps.append(dict(path=name,reason=type(e).__name__))
 archive_rows=[]
 for name in archives:
  try:
   p=REPO/name;archive_rows.append(dict(path=name,bytes=p.stat().st_size,filename_alias_hints=[a for a in aliases if a in name.lower()],introduced_staging=introduced(name),payload_read=False,admission='UNINDEXED_PAYLOAD_NOT_CERTIFIED_CLEAN'))
  except OSError as e:gaps.append(dict(path=name,reason=type(e).__name__))
 drift=[]
 for name,record in snapshot.items():
  p=REPO/name
  if not p.exists() or sha(p)!=record['sha256']:drift.append(name)
 result=dict(status='selected_nonJSON_sources_scanned_strict_family_pending',bindings=protocol['bindings'],metadata_files=len(paths),stable_files=len(snapshot),prior_scope_files=sum(not introduced(n) for n in snapshot),prior_alias_or_exact_hash_hits=hits,introduced_staging_records=introduced_records,snapshot=snapshot,unresolved=gaps,changed_before_finish=drift,archive_filename_records=archive_rows,archive_payloads_read=0,strict_unseen_families_certified=0,new_native_labels_read=False,external_history_response='pending_no_response_assumed',scope=protocol['scope'])
 with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(dict(metadata_files=len(paths),prior_hits=len(hits),introduced_files=len(introduced_records),archives=len(archive_rows),unresolved=len(gaps),drift=len(drift),strict_unseen=0)),flush=True)
if __name__=='__main__':main()
