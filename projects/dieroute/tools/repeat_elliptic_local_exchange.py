"""Five isolated deterministic replays of frozen local-exchange search only."""
from pathlib import Path
import hashlib,json,os,subprocess,time
R=Path(__file__).resolve().parents[1];D=R/'work/elliptic_local_exchange_repeats_20261020';B=R/'work/elliptic_local_exchange_20261020'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 protocol=json.loads((D/'protocol.json').read_text())
 for f,h in protocol['source_sha256'].items():assert sha(f)==h,f
 expected=json.loads((B/'manifest.json').read_text());hashes={a['name']:a['candidate_tree_sha256'] for a in expected['arms']};receipts=[]
 for i in range(5):
  folder=D/str(i);folder.mkdir();(folder/'protocol.json').write_bytes((B/'protocol.json').read_bytes());runner=folder/'run.py';runner.write_text('from pathlib import Path\nimport sys\nsys.path.insert(0,'+repr(str(R/'tools'))+')\nimport run_elliptic_local_exchange as job\njob.D=Path(__file__).resolve().parent\njob.main()\n');start=time.monotonic_ns()
  with (folder/'run.log').open('x') as log:rc=subprocess.run(['python3',str(runner)],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
  assert rc==0;state=json.loads((folder/'manifest.json').read_text());assert state['status']=='four_local_exchange_arms_terminal_require_review';actual={a['name']:sha(a['candidate_tree']) for a in state['arms']};assert actual==hashes
  receipts.append({'repeat':i,'wall_ns':time.monotonic_ns()-start,'candidate_hashes':actual,'manifest_sha256':sha(folder/'manifest.json')})
 result={'status':'five_isolated_local_exchange_search_replays_byte_identical','repeats':receipts,'arms_each':4,'unique_candidates_each':3,'source_sha256':{str(D/'protocol.json'):sha(D/'protocol.json'),str(B/'manifest.json'):sha(B/'manifest.json'),str(Path(__file__).resolve()):sha(Path(__file__).resolve())},'scope':'Local criticalpath/blocker search and tree serialization only. Frozen original native evidence not rerun. This does not satisfy full-router five-repeat closure,statistical timing,hardware or general quality requirements.','research_complete':False}
 with (D/'audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({'status':result['status'],'repeat_seconds':[v['wall_ns']/1e9 for v in receipts]}))
if __name__=='__main__':main()
