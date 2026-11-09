"""Review a matched full-workspace CPU/hw_emu bounded-search pair."""
import hashlib,json,re,struct
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_sharded_quotient_budget16_diagnostic_20261015';C=R/'work/native_fullgraph_cpu16_reference_20261015';cache={}
def sha(f):
 f=str(Path(f).resolve())
 if f not in cache:
  h=hashlib.sha256()
  with Path(f).open('rb') as v:
   for b in iter(lambda:v.read(1048576),b''):h.update(b)
  cache[f]=h.hexdigest()
 return cache[f]
def load(f):return json.loads(Path(f).read_text())
def refs(x):
 for field in ['source_sha256','input_source_sha256']:
  for f,h in x.get(field,{}).items():assert sha(f)==h,f

def main():
 p=load(P/'protocol.json');c=load(C/'protocol.json');m=load(P/'manifest.json');n=load(C/'manifest.json')
 assert m['status']=='diagnostic_exited_requires_review' and m['returncode']==0
 assert n['status']=='terminal_requires_review' and n['returncode']==0
 refs(p);refs(c);refs(load(P/'launch_protocol.json'))
 assert p['command'][1:9]==c['command'][1:9] and p['command'][10:]==c['command'][10:]
 assert p['maximum_expansions']==16 and p['label_capacity']==2097152 and p['environment']['XCL_EMULATION_MODE']=='hw_emu'
 for name in ['result.raw','metadata.raw','observations.raw']:assert sha(P/'artifacts'/name)==sha(C/'artifacts'/name),name
 result=struct.unpack('<8Q',(P/'artifacts/result.raw').read_bytes());meta=struct.unpack('<8Q',(P/'artifacts/metadata.raw').read_bytes());goal=struct.unpack('<8Q',(P/'artifacts/goal.raw').read_bytes());assert result[0]==2 and result[1]==16 and meta[:3]==result[4:7] and not any(goal);assert (P/'artifacts/observations.raw').stat().st_size==meta[1]*64
 log=(P/'run.log').read_text();markers=['native initialization verified_bytes=4482650920','DIAG seed_begin index=0','DIAG seed_wait_complete index=0','DIAG snapshot_begin limit=16','DIAG snapshot_wait_complete'];positions=[log.index(s) for s in markers];assert positions==sorted(positions)
 timers={kind:int(value) for kind,value in re.findall(r'DIAG (seed|snapshot)_enqueue_wait_wall_ns=(\d+)',log)};assert set(timers)=={'seed','snapshot'}
 for f in [P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'run.log',P/'stdout.log',P/'artifacts/goal.raw',C/'protocol.json',C/'manifest.json',C/'stdout.log',C/'stderr.log',Path(__file__).resolve()]:sha(f)
 report=dict(status='full_workspace_hw_emu16_expansions_byte_match_CPU_reference',result_words=result,observations=meta[1],labels=meta[2],enqueue_wait_wall_ns=timers,source_sha256=cache,scope='Actual hw_emu seed/snapshot at16-expansion budget with full original CSR/2Mlabels/2GiBjournal/quotient. Result, metadata and ordered journal byte-match same-source CPU reference. Host enqueue-and-wait wall times include shared-host emulation overhead; no FPGA timing, extrapolation, full search/commit or physical result.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
