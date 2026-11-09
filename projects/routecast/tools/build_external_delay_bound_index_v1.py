"""Private corrected native delay bound indexing, applies symmetrically both arms."""
import json,hashlib,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'build/native_external_seed_delay_handoff_v1_2026-10-19';A=R/'experiments/prospective_external_family_native_delay_bound_index_audit_v1_2026-10-19';D=R/'build/native_external_delay_bound_index_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 a=json.loads((A/'verification.json').read_text());assert a['exact_object_bytes_equal'];assert all(sha(p)==h for p,h in a['bindings'].items());p=json.loads((B/'protocol.json').read_text());b=json.loads((B/'receipt.json').read_text());assert sha(b['binary'])==b['binary_sha256'];assert all(sha(p)==h for p,h in b['bindings'].items());D.mkdir(exist_ok=False);(D/'source').mkdir()
 src=next(Path(k) for k in a['bindings'] if k.endswith('/connection_based_routing.cpp'));text=src.read_text();assert text.count('[ipin - 1]')==4;text=text.replace('[ipin - 1]','[ipin]');f=D/'source/connection_based_routing.cpp';f.write_text(text);shutil.copyfile(src.with_suffix('.h'),f.with_suffix('.h'))
 cp=json.loads((A/'protocol.json').read_text())['compile'];compile=cp[:-4]+['-c',str(f),'-o',str(D/'connection_based_routing.o')];link=[str(D/'sequence_vpr') if x==str(B/'sequence_vpr') else x for x in p['link']];link.insert(1,str(D/'connection_based_routing.o'))
 bindings={str(A/'verification.json'):sha(A/'verification.json'),str(B/'receipt.json'):sha(B/'receipt.json'),str(f):sha(f),str(f.with_suffix('.h')):sha(f.with_suffix('.h')),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 (D/'protocol.json').write_text(json.dumps(dict(compile=compile,link=link,bindings=bindings,policy='Only four lower_bound_connection_delay accesses within forcibly_reroute_connections use ipin instead of ipin-1; initialize/update retain original ipin. All6 fixed cold/seed same corrected native binary. Original baseline preserved; native fairness requires comparison against corrected cold, not only old cold. All physical/canonical/QoR/full timing and forecast gates unchanged.'),indent=2)+'\n')
 for name,cmd in [('compile',compile),('link',link)]:
  with (D/(name+'.log')).open('x') as out:subprocess.run(cmd,cwd=R,stdout=out,stderr=subprocess.STDOUT,check=True)
 assert all(sha(p)==h for p,h in bindings.items());bindings[str(D/'connection_based_routing.o')]=sha(D/'connection_based_routing.o');(D/'receipt.json').write_text(json.dumps(dict(binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('BUILT_FIXED_INDEX_RUNTIME_PENDING')
if __name__=='__main__':main()
