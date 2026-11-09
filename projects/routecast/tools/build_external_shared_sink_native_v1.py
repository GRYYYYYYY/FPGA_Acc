"""Link contract-verified own-index/group-OR native object with full native router."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];B=R/'build/native_external_delay_bound_index_v1_2026-10-19';F=R/'build/native_shared_sink_contract_v3_2026-10-19';V=R/'experiments/native_shared_sink_contract_v3_2026-10-19/verification.json';D=R/'build/native_external_shared_sink_native_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 v=json.loads(V.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());b=json.loads((B/'receipt.json').read_text());assert sha(b['binary'])==b['binary_sha256'];assert all(sha(k)==h for k,h in b['bindings'].items());p=json.loads((B/'protocol.json').read_text());D.mkdir(exist_ok=False);link=[str(F/'group_or.o') if x==str(B/'connection_based_routing.o') else str(D/'sequence_vpr') if x==str(B/'sequence_vpr') else x for x in p['link']];bindings={str(V):sha(V),str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)}
 for x in link:
  if x.startswith('/') and Path(x).is_file():bindings[x]=sha(x)
 (D/'protocol.json').write_text(json.dumps(dict(link=link,bindings=bindings,policy='Full native router with own-index lower bounds plus perNET force-flag reset/group OR object proven by actual native fixtures. No criticality substitution/wrap in full native link. Symmetric cold/seed all3; current alias-free cohort must reproduce own-index baseline. All original forecast/native utility gates retained.'),indent=2)+'\n')
 with (D/'link.log').open('x') as log:subprocess.run(link,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(binary=str(D/'sequence_vpr'),binary_sha256=sha(D/'sequence_vpr'),bindings=bindings),indent=2)+'\n');print('FULL_NATIVE_GROUP_OR_BUILT')
if __name__=='__main__':main()
