"""Stream nonZIP archive headers; do not extract or interpret member contents."""
import hashlib,json,tarfile,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];REPO=R.parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 zp=R/'experiments/prospective_external_family_archive_index_v1_2026-10-18/verification.json';z=json.loads(zp.read_text());out=R/'experiments/prospective_external_family_tar_index_v1_2026-10-18';out.mkdir(exist_ok=False);aliases=['chacha','xchacha','salsa','salsa20','poly1305','blabla'];rows=[]
 targets=z['unresolved'];assert len(targets)==2 and all(x['reason']=='nonZIP_payload_not_opened' for x in targets)
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings={str(zp):sha(zp),str(Path(__file__)):sha(__file__)},archives=targets,scope='Streaming tar header names/sizes/types only. Compression bytes must be decoded to reach headers, but no member is extracted, opened as a file object, or interpreted as RTL/netlist/route/label content. Directory absence is not an ancestry or history certificate.'),f,indent=2)
 for target in targets:
  path=REPO/target['path'];before=path.stat();start=time.perf_counter();records=[]
  with tarfile.open(path,mode='r|*') as tar:
   for entry in tar:records.append((entry.name,entry.size,entry.type.decode('ascii','replace')))
  after=path.stat();stable=(before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_size,after.st_mtime_ns,after.st_ctime_ns)
  row=dict(path=target['path'],archive_bytes=after.st_size,entries=len(records),members=records,directory_sha256=hashlib.sha256(json.dumps(records,separators=(',',':')).encode()).hexdigest(),alias_hints=[x[0] for x in records if any(a in x[0].lower() for a in aliases)],stable_during_index=stable,component_seconds=time.perf_counter()-start,member_contents_extracted_or_interpreted=0);rows.append(row)
  with (out/'progress.jsonl').open('a') as f:f.write(json.dumps({k:v for k,v in row.items() if k!='members'})+'\n')
  print('TAR DIRECTORY INDEX DONE',path.name,len(records),'stable',stable,flush=True)
 with (out/'verification.json').open('x') as f:json.dump(dict(status='both_nonZIP_directories_indexed_no_payload_history_claim',bindings={str(zp):sha(zp),str(Path(__file__)):sha(__file__)},rows=rows,alias_hints=[dict(path=r['path'],members=r['alias_hints']) for r in rows if r['alias_hints']],strict_unseen_families_certified=0,scope='All310archive directories now indexed across ZIP and tar stages, not all member source content or modification history. External-history and lineage qualification remain unresolved; no new target labels or family admission.'),f,indent=2)
if __name__=='__main__':main()
