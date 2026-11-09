"""ZIP central-directory provenance hints only; no member data decompression."""
import datetime,hashlib,json,zipfile
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=R/'experiments/prospective_external_family_nonJSON_exposure_v1_2026-10-18/verification.json';s=json.loads(source.read_text());out=R/'experiments/prospective_external_family_archive_index_v1_2026-10-18';out.mkdir(exist_ok=False);aliases=['chacha','xchacha','salsa','salsa20','poly1305','blabla'];rows=[];gaps=[]
 for record in s['archive_filename_records']:
  name=record['path'];path=REPO/name
  if not name.endswith('.zip'):gaps.append(dict(path=name,reason='nonZIP_payload_not_opened',bytes=record['bytes']));continue
  try:
   before=path.stat()
   with zipfile.ZipFile(path) as z:
    members=z.infolist();listing=sorted((x.filename,x.file_size,x.compress_size,x.CRC,x.compress_type) for x in members);hits=[x[0] for x in listing if any(a in x[0].lower() for a in aliases)];types=Counter(Path(x[0]).suffix.lower() for x in listing if x[0] and not x[0].endswith('/'))
   after=path.stat();stable=(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
   item=dict(path=name,archive_bytes=after.st_size,archive_version=dict(device=after.st_dev,inode=after.st_ino,size=after.st_size,mtime_ns=after.st_mtime_ns,ctime_ns=after.st_ctime_ns),entries=len(listing),directory_sha256=hashlib.sha256(json.dumps(listing,separators=(',',':')).encode()).hexdigest(),member_alias_hints=hits,member_suffix_counts=dict(types),stable_during_index=stable,decompressed_member_contents=0)
   rows.append(item)
   if not stable:gaps.append(dict(path=name,reason='changed_during_directory_index'))
  except (OSError,zipfile.BadZipFile,RuntimeError) as error:gaps.append(dict(path=name,reason=type(error).__name__))
 result=dict(status='ZIP_directory_index_complete_payload_history_unproved',checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_archive_count=len(s['archive_filename_records']),ZIP_archives_indexed=len(rows),ZIP_entries_indexed=sum(x['entries'] for x in rows),directory_alias_hints=[dict(path=x['path'],members=x['member_alias_hints']) for x in rows if x['member_alias_hints']],rows=rows,unresolved=gaps,strict_unseen_families_certified=0,scope='ZIP directory metadata read only, no member data opened or decompressed. Names/CRCs do not authenticate source contents or prove absence of renamed/modified ancestry. Two nonZIP archives and all member payload histories remain unverified. Not source-family admission or route/label observation.',bindings={str(source):sha(source),str(Path(__file__)):sha(__file__)})
 with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps({k:result[k] for k in ['source_archive_count','ZIP_archives_indexed','ZIP_entries_indexed','directory_alias_hints','unresolved']}),flush=True)
if __name__=='__main__':main()
