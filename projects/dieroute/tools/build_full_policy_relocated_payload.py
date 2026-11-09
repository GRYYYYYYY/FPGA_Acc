"""Copy prepared CPU workflow inputs to an independent content-deduplicated tree."""
from pathlib import Path
import json,hashlib,os,stat,time
R=Path(__file__).resolve().parents[1]
O=R/'work/full_policy_relocated_payload_20261021'
I=R/'work/full_policy_portability_inventory_20261021/inventory.json'
def main():
 assert not (O/'manifest.json').exists(),'No implicit replay'
 inventory=json.loads(I.read_text());base=Path(inventory['virtual_base']);payload=O/'payload';blobs=O/'blobs';payload.mkdir();blobs.mkdir()
 receipt={'pid':os.getpid(),'start_ticks':Path(f'/proc/{os.getpid()}/stat').read_text().rsplit(')',1)[1].split()[19]}
 (O/'launch_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 (O/'preparation.json').write_text(json.dumps({'recorded_at_launch_ns':time.time_ns(),'inventory':str(I),'inventory_sha256':hashlib.sha256(I.read_bytes()).hexdigest(),'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'virtual_base':str(base),'scope':'Independent prepared CPU workflow input copy only. No source rewriting or original experiment mutation; runtime completeness,all original repeats and portability remain unverified.','research_complete':False},indent=2)+'\n')
 files={};unique=set();logical=0;physical=0;last=0
 def save(status,**extra):
  p=O/'manifest.tmp';p.write_text(json.dumps({'status':status,'pid':os.getpid(),'copied_files':len(files),'logical_bytes':logical,'unique_blob_bytes':physical,'research_complete':False,**extra},indent=2)+'\n');p.replace(O/'manifest.json')
 save('copying_prepared_inputs')
 try:
  for name,row in inventory['files'].items():
   source=Path(name);rel=source.relative_to(base);dest=payload/rel;dest.parent.mkdir(parents=True,exist_ok=True)
   before=source.stat();mode=stat.S_IMODE(before.st_mode);h=hashlib.sha256();temporary=blobs/'.copy.tmp'
   with source.open('rb') as src,temporary.open('xb') as target:
    for block in iter(lambda:src.read(8*1024*1024),b''):h.update(block);target.write(block)
   after=source.stat();assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),name
   digest=h.hexdigest();blob=blobs/(digest+'.'+oct(mode)[2:])
   if blob.exists():temporary.unlink()
   else:temporary.chmod(mode);temporary.rename(blob);unique.add(blob.name);physical+=after.st_size
   os.link(blob,dest);logical+=after.st_size
   files[str(rel)]={'sha256':digest,'mode':mode,'bytes':after.st_size,'blob':blob.name,'original_path':name}
   if time.monotonic()-last>10:save('copying_prepared_inputs',last_copied=name);last=time.monotonic()
  with (O/'payload_manifest.json').open('x') as f:json.dump({'virtual_base':str(base),'files':files,'scope':inventory['scope'],'research_complete':False},f,indent=2);f.write('\n')
  save('prepared_payload_copied_requires_isolated_runtime_validation',unique_blobs=len(unique),unresolved_inventory_paths=inventory['missing_or_output_paths'])
  print(json.dumps({'copied_files':len(files),'logical_bytes':logical,'unique_blob_bytes':physical,'unique_blobs':len(unique)}))
 except BaseException as e:save('copy_stopped_requires_review',error=repr(e));raise
if __name__=='__main__':main()
