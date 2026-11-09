"""Live callback digests vs independent byte hashes, raw captures and native parity."""
import json,struct,subprocess,math
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_status_consumer_trial_v1_2026-10-20'
def main():
 vp=D/'verification.json';v=json.loads(vp.read_text());assert len(v['rows'])==18 and all(x['no_iteration_route_files'] and x['callback_sequence_complete'] and x['nonclock_iteration_summaries_equal'] and x['terminal_physical_sequences_equal'] for x in v['rows']);proof=E/'prince_resident_phase_trial_v1_2026-10-20/phase_verification_v1.json';bindings={str(p):sha(p) for p in [vp,proof,Path(__file__)]};source=R/'tools/hash_prince_observation_body_v1.cpp';tool=D/'body_hash';cmd=['/usr/bin/c++','-std=c++17','-O3',str(source),'-o',str(tool)]
 with (D/'hash_build.log').open('x') as f:code=subprocess.call(cmd,stdout=f,stderr=subprocess.STDOUT)
 assert code==0;bindings[str(source)]=sha(source);bindings[str(tool)]=sha(tool);results=[];count=0;rawmatches=0;consume_ns=0;capture_ns=0
 cases=sorted({r['case'].rsplit('/',1)[0] for r in v['rows']})
 for case in cases:
  before=E/'prince_resident_phase_trial_v1_2026-10-20'/case/'capture/boundary';capture=D/case/'capture';digest=D/case/'digest';a=[list(map(int,s.split())) for s in (capture/'callback.tsv').read_text().splitlines()];b=[list(map(int,s.split())) for s in (digest/'callback.tsv').read_text().splitlines()];assert len(a)==len(b)
  reference_phase=[list(map(int,s.split())) for s in (before/'phase.tsv').read_text().splitlines()];assert len(reference_phase)==len(a);paths=[]
  for i in range(1,len(a)+1):paths.extend([before/f'iteration_{i}.bin',before/f'boxes_{i}.bin'])
  hashes=list(map(int,subprocess.check_output([str(tool),*map(str,paths)],text=True).split()));assert len(hashes)==2*len(a);case_consume=case_capture=0
  for i,(x,y,pres) in enumerate(zip(a,b,reference_phase),1):
   assert len(x)==len(y)==14 and x[:11]==y[:11] and x[0]==i and x[3:7]==pres[1:5];assert x[7:9]==hashes[2*(i-1):2*i]
   raw=paths[2*(i-1)].read_bytes();n=struct.unpack_from('<Q',raw,16)[0];assert x[1]==n and x[2]==1792;elev=ch=0
   for nid,kind,occ,cap,bits in struct.iter_unpack('<QIiiI',raw[24:]):
    value=struct.unpack('<f',struct.pack('<I',bits))[0];elev+=value>1;ch+=(kind in [4,5] and value>1)
   assert x[9:11]==[elev,ch]
   for row in [x,y]:assert row[11]<=row[12]<=row[13]
   for name in [f'iteration_{i}.bin',f'boxes_{i}.bin']:
    old=before/name;new=capture/'boundary'/name;assert sha(old)==sha(new);bindings[str(old)]=sha(old);bindings[str(new)]=sha(new);rawmatches+=1
   assert not list(digest.glob('iteration_*.route')) and not (digest/'boundary').exists();count+=1;case_consume+=y[12]-y[11];case_capture+=x[13]-x[12]
  assert (capture/'boundary/phase.tsv').read_bytes()==(before/'phase.tsv').read_bytes();consume_ns+=case_consume;capture_ns+=case_capture;results.append(dict(case=case,boundaries=len(a),digest_consumer_compute_ns=case_consume,capture_arm_optional_export_ns=case_capture))
  for p in [capture/'callback.tsv',digest/'callback.tsv',before/'phase.tsv',capture/'boundary/phase.tsv']:bindings[str(p)]=sha(p)
 assert count==227 and rawmatches==454 and all(sha(p)==h for p,h in bindings.items());(D/'consumer_verification_v1.json').write_text(json.dumps(dict(status='ALL18_NO_ROUTE_SNAPSHOT_RUNS_AND227_SYNCHRONOUS_CONSUMER_BOUNDARIES_PASS',cases=results,boundaries=count,raw_capture_payloads_equal=rawmatches,digest_consumer_compute_seconds=consume_ns/1e9,capture_arm_optional_export_seconds=capture_ns/1e9,bindings=bindings,scope='Live const state consumption at original status boundary without iteration route files. Digest/capture summaries and FNV1a checksums agree with independently hashed original verified payload bodies; checksums are noncryptographic. Capture arm all RR/BB bytes and phase rows exactly match previous snapshot observations. Original terminal physical sequences and nonclock iteration summaries preserved in all18 runs. Subclocks exclude callback ledger append; native/full process clocks include it. No stop/restore, prediction quality, cryptographic state identity or complete matched workflow gain.'),indent=2)+'\n');print('LIVE_STATUS_CONSUMER_PASS',count,rawmatches,'compute_s',consume_ns/1e9,'capture_s',capture_ns/1e9)
if __name__=='__main__':main()
