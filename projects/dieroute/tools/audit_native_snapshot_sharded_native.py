"""Compare three-isolated-bank native C-model outputs to audited flat outputs."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
run,gold=map(Path,sys.argv[1:3])
m=json.loads((run/'manifest.json').read_text());assert m['returncode']==0 and m['inputs_unchanged']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
for p,h in m['inputs'].items():assert sha(Path(p))==h
r=json.loads((run/'stdout.log').read_text());assert r==m['result'] and r['status']=='passed' and r['search_status']==0
assert json.loads((gold/'path_audit.json').read_text())['status']=='passed'
art=run/'artifacts';names=['result.raw','goal.raw','observations.raw','attachment.raw','path_nodes.raw','path_pips.raw'];hashes={}
for name in names:
 h=sha(art/name);assert h==sha(gold/name),name;hashes[name]=h
trace=re.findall(r'^reference complete expanded=(\d+) reads=(\d+)$',(run/'run.log').read_text(),re.M)
assert trace==[(str(r['expanded']),str(r['observations']))]
assert re.search(r'\bT dieroute_native_snapshot_search_sharded_hbm$',subprocess.check_output(['nm','--defined-only',m['command'][0]],text=True),re.M)
report=dict(status='passed',result=r,artifact_hashes=hashes,
 scope='Actual three-bank whole-search top C-model on native graph; separate owner arrays/padding byte assertions, independent SparseSearch counters and exact flat artifact equality',
 limitations=['Imported immutable authority','No actual bank placement, RTL large graph, concurrent owner or board result'],board_result=False)
(run/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status='passed',result=r)))
