"""Review a same-source CPU reference, without treating it as hardware validation."""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];P=R/'work/native_fullgraph_cpu256_oracle_20261015';cache={}
def sha(q):
 q=str(Path(q).resolve())
 if q not in cache:
  h=hashlib.sha256()
  with Path(q).open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[q]=h.hexdigest()
 return cache[q]
def main():
 p=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='terminal_requires_review' and m['returncode']==0
 for field in ['source_sha256','input_source_sha256']:
  for q,h in p[field].items():assert sha(q)==h,q
 x=json.loads((R/'work/native_sharded_quotient_budget256_diagnostic_20261015/protocol.json').read_text());assert p['command'][1:9]==x['command'][1:9] and p['command'][10:]==x['command'][10:]
 frozen=R/'work/native_sharded_quotient_budget256_diagnostic_20261015/source/include';count=0
 for f in (P/'include').glob('*.hpp'):
  assert sha(f)==sha(frozen/f.name),f;count+=1
 a=P/'artifacts';result=struct.unpack('<8Q',(a/'result.raw').read_bytes());meta=struct.unpack('<8Q',(a/'metadata.raw').read_bytes());assert result==(2,256,1445,1451,843,1421,1099,0) and meta[:3]==result[4:7] and not any(meta[3:]);assert (a/'observations.raw').stat().st_size==meta[1]*64
 for f in [P/'protocol.json',P/'manifest.json',P/'run.py',P/'stdout.log',P/'stderr.log',*a.glob('*.raw'),Path(__file__).resolve()]:sha(f)
 report=dict(status='same_source_fullgraph_cpu_reference_returns_budget_after256_expansions',result_words=result,metadata_words=meta,matching_frozen_headers=count,source_sha256=cache,scope='CPU executes the same frozen snapshot/seed/quotient source headers and matching full input arguments, with lazily resident zero scratch. All bound source/input hashes rechecked. Reference counters support comparison with future hw_emu output, not an independent algorithm proof, hardware correctness, physical performance, full path or commit completion. Wall time includes parsing/CRC/quotient and is not a hardware timing comparison.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
