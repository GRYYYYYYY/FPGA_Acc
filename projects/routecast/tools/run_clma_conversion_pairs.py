"""Sequential AB/BA fresh-process cold conversion preparation comparison."""
import json,time,subprocess,sys,shutil,hashlib
from pathlib import Path
ROOT=Path('experiments/clma_conversion_pairs_2026-10-05')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def worker(root,label,fast):
 sys.path.insert(0,str((root/'source').resolve()))
 from streaming_bound_csr import convert
 p=json.loads((root/'protocol.json').read_text());inputs=p['inputs'];out=root/label;out.mkdir()
 assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
 start=time.monotonic();m=convert(inputs['graph']['path'],Path(inputs['table']['path']).read_text(),Path(inputs['binding']['path']).read_text(),p['identity'],out/'csr',class_cache=fast)
 seconds=time.monotonic()-start;reference=json.loads(Path(p['reference_manifest']['path']).read_text());assert m==reference
 for f in m['files'].values():assert sha(out/'csr'/f['file'])==f['sha256']
 assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
 r={'class_cache':fast,'conversion_wall_s':seconds,'manifest_exact':True,'all_payload_hashes_exact':True,'inputs_unchanged':True};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
def main():
 if ROOT.exists():raise ValueError('fresh output required')
 reference=Path('experiments/clma_prepared_csr_2026-10-04');p=json.loads((reference/'protocol.json').read_text());m=json.loads((reference/'csr/manifest.json').read_text())
 assert all(sha(v['path'])==v['sha256'] for v in p['inputs'].values())
 ROOT.mkdir();(ROOT/'source').mkdir()
 for f in Path('tools').glob('*.py'):shutil.copyfile(f,ROOT/'source'/f.name)
 protocol={'inputs':p['inputs'],'identity':m['context']['cost_identity'],'reference_manifest':{'path':str((reference/'csr/manifest.json').resolve()),'sha256':sha(reference/'csr/manifest.json')},'order':[['A1',False],['B1',True],['B2',True],['A2',False]],'source_sha256':{f.name:sha(f) for f in (ROOT/'source').glob('*.py')},'scope':'two fresh-process AB/BA pairs of full cold additive CSR conversion; shared host uncontrolled, excludes search/feedback/native routing and offline audit time'}
 (ROOT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic();results=[]
 for label,fast in protocol['order']:
  print(json.dumps({'starting':label,'class_cache':fast}),flush=True)
  command=[sys.executable,str((ROOT/'source'/Path(__file__).name).resolve()),'--worker',str(ROOT.resolve()),label,str(int(fast))]
  with (ROOT/(label+'_stdout.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=600)
  assert r.returncode==0,(label,r.returncode)
  receipt=json.loads((ROOT/label/'receipt.json').read_text());results.append({'label':label,**receipt});print(json.dumps(results[-1]),flush=True)
 assert all(sha(ROOT/'source'/n)==h for n,h in protocol['source_sha256'].items())
 assert sha(protocol['reference_manifest']['path'])==protocol['reference_manifest']['sha256']
 ratios=[results[0]['conversion_wall_s']/results[1]['conversion_wall_s'],results[3]['conversion_wall_s']/results[2]['conversion_wall_s']]
 result={'results':results,'paired_ratios':ratios,'full_wall_s':time.monotonic()-start,'protocol_sha256':sha(ROOT/'protocol.json'),'scope':protocol['scope']};(ROOT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
if __name__=='__main__':
 if len(sys.argv)>1:worker(Path(sys.argv[2]),sys.argv[3],bool(int(sys.argv[4])))
 else:main()
