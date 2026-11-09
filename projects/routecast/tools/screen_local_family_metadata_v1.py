"""Bounded source-reference inventory; never absence-to-unseen admission."""
import hashlib,json,re,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'local_family_metadata_screen_v1_2026-10-20'
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 D.mkdir(exist_ok=False);vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/benchmarks';sources=sorted(p for sub in ['freecores','verilog','ultraembedded'] for p in (vendor/sub).glob('*.v'));source_rows=[{'path':str(p),'filename':p.name,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size} for p in sources]
 command=['rg','--files','experiments','-g','protocol.json','-g','*manifest*.json','-g','*source*inventory*.json','-g','*cases*.json'];paths=sorted(set(subprocess.check_output(command,cwd=R,text=True).splitlines()));metadata=[];hits={r['path']:[] for r in source_rows};omitted=[]
 patterns={r['path']:re.compile(r'(?<![A-Za-z0-9_])'+re.escape(r['filename'])+r'(?![A-Za-z0-9_])',re.I) for r in source_rows}
 for name in paths:
  p=R/name;before=p.stat()
  if before.st_size>2**21:omitted.append({'path':name,'bytes':before.st_size,'reason':'above_fixed2MiB_scan_bound'});continue
  data=p.read_bytes();digest=sha(data);text=data.decode('utf-8','replace');changed=before.st_mtime_ns!=p.stat().st_mtime_ns or before.st_size!=p.stat().st_size;metadata.append({'path':name,'sha256':digest,'bytes':len(data),'changed_during_read':changed})
  if changed:omitted.append({'path':name,'reason':'changed_during_read'});continue
  for r in source_rows:
   filename=bool(patterns[r['path']].search(text));exact=r['sha256'] in text
   if filename or exact:hits[r['path']].append({'metadata':name,'metadata_sha256':digest,'filename_reference':filename,'exact_digest_reference':exact})
 for r in source_rows:
  r['references']=hits[r['path']];r['reference_count']=len(r['references']);r['strict_unseen_admitted']=False;r['classification']='HISTORICAL_METADATA_REFERENCE_FOUND' if r['references'] else 'NO_REFERENCE_IN_BOUNDED_SELECTED_METADATA_NOT_UNSEEN_CERTIFIED'
 result={'status':'BOUNDED_LOCAL_SOURCE_REFERENCE_SCREEN_COMPLETE_NO_FAMILY_ADMITTED','observed_unix':time.time(),'source_rows':source_rows,'selected_metadata_count':len(paths),'scanned_metadata_count':len(metadata),'metadata':metadata,'unresolved':omitted,'command':command,'bindings':{str(Path(__file__)):sha(Path(__file__).read_bytes())},'scope':'Read-only39 local HDL sources and selected RouteCast JSON metadata only. Filename/hash reference proves declaration/reference, not actual training, label exposure, successful execution, family independence or source semantics. Excludes tools/free text/large metadata/root archives/other project histories and derivatives. No synthesis/place/route/target labels read or produced. Absence cannot admit unseen. No benchmark selected by result.'};(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('LOCAL_SOURCE_REFERENCE_SCREEN_COMPLETE','sources',len(source_rows),'metadata',len(metadata),'unresolved',len(omitted),'referenced',sum(r['reference_count']>0 for r in source_rows))
if __name__=='__main__':main()
