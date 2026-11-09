"""Independent publisher replay and valid-CRC adversarial capture edits."""
import argparse,json,struct,subprocess,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'))
from audit_owner_publish_replay import verify
from audit_native_label_transport import crc64

def main():
 ap=argparse.ArgumentParser()
 for name in ('router','parallel-router','quotient-builder','publisher'):ap.add_argument('--'+name,type=Path,required=True)
 ap.add_argument('--output',type=Path);a=ap.parse_args()
 scratch=None
 if a.output is None:scratch=tempfile.TemporaryDirectory();a.output=Path(scratch.name)/'cases'
 a.output.mkdir(parents=True,exist_ok=False)
 result=subprocess.run([sys.executable,str(root/'tb/native_cohort_test.py'),'--router',str(a.router.resolve()),'--parallel-router',str(a.parallel_router.resolve()),'--quotient-builder',str(a.quotient_builder.resolve()),'--output',str(a.output/'input')],capture_output=True,text=True);assert result.returncode==0,result.stderr
 results=[]
 for period in (1,3):
  source=a.output/'input'/f'summary_hbm_{period}'/'route';out=a.output/f'publisher_{period}'
  command=[str(a.publisher.resolve()),str(source/'summary_hbm_frames.bin'),str(source/'summary_hbm_topology.bin'),'0123456789abcdef0123456789abcdef','2',str(out)]
  result=subprocess.run(command,capture_output=True,text=True);assert result.returncode==0,result.stderr
  proof=verify(out,source,2);assert proof['passed'];(out/'audit.json').write_text(json.dumps(proof,indent=2)+'\n')
  path=out/'events.bin';original=path.read_bytes()
  for kind,word in ((0,32),(0,26),(1,26),(1,8),(2,12),(1,1)):
   damaged=bytearray(original);changed=0
   for offset in range(64,len(damaged),384):
    words=list(struct.unpack_from('<48Q',damaged,offset))
    if words[5]==kind:words[word]+=1;struct.pack_into('<48Q',damaged,offset,*words);changed+=1
   assert changed;struct.pack_into('<Q',damaged,48,crc64(damaged[64:]));path.write_bytes(damaged);rejected=False
   try:verify(out,source,2)
   except AssertionError:rejected=True
   finally:path.write_bytes(original)
   assert rejected,(kind,word)
  results.append(dict(period=period,passed=True,semantic_mutations_rejected=6,events=proof['events']))
 (a.output/'audit.json').write_text(json.dumps(dict(passed=True,cases=results),indent=2)+'\n');print('owner publisher independent replay and 12 valid-CRC semantic mutations passed')
if __name__=='__main__':main()
