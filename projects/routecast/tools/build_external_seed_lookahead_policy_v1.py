"""Isolated external seed LOOKAHEAD policy ablation; preserves retained/nonlookahead."""
import json,hashlib,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
B=R/'build/native_external_initial_response_observer_v2_2026-10-19'
D=R/'build/native_external_seed_lookahead_policy_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=json.loads((B/'protocol.json').read_text());receipt=json.loads((B/'receipt.json').read_text())
 assert sha(receipt['binary'])==receipt['binary_sha256']
 assert all(sha(k)==v for k,v in p['bindings'].items())
 D.mkdir(exist_ok=False);shutil.copytree(B/'source',D/'source')
 f=D/'source/route.cpp';s=f.read_text();a='        if (retained_input || (routecast_seed && *routecast_seed)) {'
 assert s.count(a)==1;s=s.replace(a,'        if (retained_input) {',1);f.write_text(s)
 compile=[x.replace(str(B),str(D)) for x in p['compile']];link=[x.replace(str(B),str(D)) for x in p['link']]
 bindings={str(B/'protocol.json'):sha(B/'protocol.json'),str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 for f in (D/'source').rglob('*'):
  if f.is_file():bindings[str(f)]=sha(f)
 protocol=dict(compile=compile,link=link,bindings=bindings,policy='External seed under LOOKAHEAD retains lookahead delays before initial STA. Same-process retained_input and nonlookahead seed delays unchanged. Trees/occupancy retained. Observer initial perpin and first iteration outputs unchanged.',scope='All3 fixed cold/seed native-only pilot. Full physical/canonical,15616 required CIDs,CPD and wirelength nonregress. No percase selection or full paid timing acceptance. Cold equivalence and initial cold/seed perpin equality pending.')
 (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as out:subprocess.run(cmd,cwd=R,stdout=out,stderr=subprocess.STDOUT,check=True)
 assert all(sha(k)==v for k,v in bindings.items())
 (D/'receipt.json').write_text(json.dumps(dict(status='BUILT_RUNTIME_VERIFICATION_PENDING',binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('BUILT_RUNTIME_VERIFICATION_PENDING',flush=True)
if __name__=='__main__':main()
