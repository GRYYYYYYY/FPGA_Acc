"""Review real new-path CPU publication with flat/sharded byte differentials."""
import hashlib,json,re,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_identity_higher_g_commit_differential_20261015'
def sha(f):
 h=hashlib.sha256()
 with Path(f).open('rb') as v:
  for b in iter(lambda:v.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='terminal_requires_review' and m['returncode']==0
 for obj in [p,json.loads((P/'launch_protocol.json').read_text())]:
  for field in ['source_sha256','input_source_sha256']:
   for f,h in obj.get(field,{}).items():assert sha(f)==h,f
 text=(P/'stdout.log').read_text();values=[json.loads(v) for v in text.splitlines() if v.startswith('{')];assert len(values)==1;r=values[0];assert r['status']=='passed' and r['commit_calls']==1 and r['query_calls']==42 and r['canonical_reads']==256
 counts=re.findall(r'SHARDED_DIFFERENTIAL calls=(\d+) isolated_owner_banks=(\d+)',text);assert counts==[('43','3')]
 symbols=subprocess.check_output(['nm','--defined-only',str(Path(p['command'][0]))],text=True)
 for symbol in ['dieroute_net_commit_hbm','dieroute_net_commit_flat_reference','dieroute_net_commit_sharded_hbm']:assert re.search(r'\bT '+symbol+r'\b',symbols),symbol
 q=json.loads((P/'artifacts/independent_audit.json').read_text());assert q['status']=='passed' and q['published_nodes']==42 and q['all_net_trees_checked']==341
 assert sha(Path(p['command'][0]).with_name('flat.cpp'))=='84d5550636cd7bfd12b34176294ca29bd57c0cc15e2a17e11a3c6de32252260c'
 files=[P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'stdout.log',P/'stderr.log',P/'independent_review.stdout',P/'artifacts/independent_audit.json',*P.joinpath('artifacts').glob('*.raw'),Path(__file__).resolve()]
 report=dict(status='new_identity_higher_g_path_CPU_flat_sharded43call_byte_differential_and_global_state_reviewed',published_nodes=42,canonical_reads=256,differential_calls=43,independent_owner_banks=3,all_net_trees_checked=341,new_revision=r['revision'],source_sha256={str(f):sha(f) for f in files},scope='Actual newly selected original-task path, unchanged protected flat core versus three guarded sharded owner arrays. Entire authority/scratch/delta/completion buffers byte-compared on proposal and42queries; independent all-tree/resource/version/revision replay passes. CPU serialized C-model only; no actual bank placement, XRT execution, crash atomicity, full cohort quality or performance proof.',adopted=False,board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
