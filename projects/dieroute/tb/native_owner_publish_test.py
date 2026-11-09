"""Fresh push-mode search, exact differential and semantic capture corruptions."""
import argparse,csv,json,struct,subprocess,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'tools'))
from audit_native_parallel import verify
from audit_native_summary_hbm import SummaryEndpointAudit
from audit_native_label_transport import crc64

def main():
 ap=argparse.ArgumentParser()
 for n in ('router','parallel-router','quotient-builder'):ap.add_argument('--'+n,type=Path,required=True)
 ap.add_argument('--output',type=Path);a=ap.parse_args();scratch=None
 if a.output is None:scratch=tempfile.TemporaryDirectory();a.output=Path(scratch.name)/'cases'
 a.output.mkdir(parents=True,exist_ok=False)
 r=subprocess.run([sys.executable,str(root/'tb/native_cohort_test.py'),'--router',str(a.router.resolve()),'--parallel-router',str(a.parallel_router.resolve()),'--quotient-builder',str(a.quotient_builder.resolve()),'--output',str(a.output/'input')],capture_output=True,text=True);assert r.returncode==0,r.stderr
 results=[]
 for period in (1,3):
  source=a.output/'input'/f'summary_hbm_{period}';command=json.loads((source/'command.json').read_text());out=a.output/f'push_{period}';out.mkdir();command[7]=str(out/'route');command[23]='2'
  r=subprocess.run(command,capture_output=True,text=True);(out/'run.log').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
  (out/'command.json').write_text(json.dumps(command,indent=2)+'\n');proof=verify(out,{'command':command});assert proof['summary_hbm']['owner_publisher']['enabled'] and proof['persistent_shadows']['totals']['publication_scans']==0
  invalid=list(command);invalid[23]='3';rejected=False
  try:verify(out,{'command':invalid})
  except AssertionError:rejected=True
  assert rejected,'unknown endpoint mode skipped protocol audit'
  equal=[]
  for p in (source/'route').iterdir():
   if p.name in ('audit.json','execution.csv','summary_hbm_frames.bin','persistent_shadow_publications.csv'):continue
   assert p.read_bytes()==(out/'route'/p.name).read_bytes(),p.name;equal.append(p.name)
  def records(p):
   with p.open() as f:return list(csv.DictReader(f))
  before=records(source/'route/persistent_shadow_publications.csv');after=records(out/'route/persistent_shadow_publications.csv')
  assert len(before)==len(after)
  for x,y in zip(before,after):assert y.pop('scans')=='0';x.pop('scans');assert x==y
  path=out/'route/summary_hbm_frames.bin';original=path.read_bytes()
  for reason,word in ((0,17),(0,26),(0,32),(1,10),(4,8),(4,26),(4,36),(5,12),(5,16),(5,13)):
   damaged=bytearray(original);changed=0
   for off in range(64,len(damaged),384):
    words=list(struct.unpack_from('<48Q',damaged,off))
    if words[5]==reason:words[word]+=1;struct.pack_into('<48Q',damaged,off,*words);changed+=1
   assert changed;struct.pack_into('<Q',damaged,48,crc64(damaged[64:]));path.write_bytes(damaged);rejected=False
   try:verify(out,{'command':command})
   except AssertionError:rejected=True
   finally:path.write_bytes(original)
   assert rejected,(reason,word)
  # A legal endpoint transcript assigned to the wrong commit boundary still
  # has to fail the outer native coordinator replay.
  damaged=bytearray(original)
  for off in range(64,len(damaged),384):
   words=list(struct.unpack_from('<48Q',damaged,off))
   if words[5]==1 and words[1]==words[2]==words[4]==0:words[1]=0xffffffff;words[2]=1;struct.pack_into('<48Q',damaged,off,*words)
  struct.pack_into('<Q',damaged,48,crc64(damaged[64:]));path.write_bytes(damaged);rejected=False
  try:
   SummaryEndpointAudit(out/'route',command)
   try:verify(out,{'command':command})
   except AssertionError:rejected=True
  finally:path.write_bytes(original)
  assert rejected,'publisher installation detached from coordinator state'
  (out/'audit.json').write_text(json.dumps(proof,indent=2)+'\n');results.append(dict(period=period,passed=True,equal_files=equal,valid_crc_mutations_rejected=10,wrong_commit_boundary_rejected=True))
 (a.output/'audit.json').write_text(json.dumps(dict(passed=True,cases=results),indent=2)+'\n');print('fresh native publisher routing differential, 20 valid-CRC mutations and 2 commit-boundary corruptions passed')
if __name__=='__main__':main()
