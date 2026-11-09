"""Compare actual native search CU artifacts with audited C-model artifacts."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
run,gold,build=map(Path,sys.argv[1:4])
m=json.loads((run/'manifest.json').read_text());assert m['returncode']==0 and m['inputs_unchanged']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()
for p,h in m['inputs'].items():assert sha(Path(p))==h
bank_audit=json.loads((build/'group_audit/audit.json').read_text());assert bank_audit['status']=='sharded_groups_verified_runtime_ownership_pending' and bank_audit['pointer_arguments']==39
values=[json.loads(line) for line in (run/'stdout.log').read_text().splitlines() if line.startswith('{')]
assert len(values)==1;r=values[0];assert r==m['result'] and r['status']=='executed' and r['snapshot_calls']==1 and r['authority_imports']==1 and r['authority_reuploads']==0
snap=Path(m['command'][1]);meta=json.loads((snap/'snapshot.json').read_text());assert r['seed_calls']==meta['seed_count']
assert r['owner_groups']==[bank_audit['allocation_role_group_ids']['owner'+str(i)] for i in range(3)]==[13,14,15]
assert int(m['command'][5])==meta['net_slot'] and int(m['command'][6])==meta['sink']
assert json.loads((gold/'path_audit.json').read_text())['status']=='passed'
art=run/'artifacts';names=['result.raw','goal.raw','observations.raw','attachment.raw','path_nodes.raw','path_pips.raw'];hashes={}
for name in names:
 h=sha(art/name);assert h==sha(gold/name),name;hashes[name]=h
search=Path(m['command'][2]);policy=Path(m['command'][3]);expected=sum((search/n).stat().st_size-64 for n in ['offsets.bin','arcs.bin'])+policy.stat().st_size-64
expected+=sum((snap/n).stat().st_size for n in ['resources.raw','trees.raw','nets.raw','control.raw'])
if len(m['command'])==11:expected+=meta['config'][0]*8
assert r['verified_upload_bytes']==expected
symbols=subprocess.check_output(['nm','--defined-only',m['command'][0]],text=True)
assert not re.search(r'\bT dieroute_(?:native_snapshot_search_sharded_hbm|native_search_worker_hbm|net_commit_sharded_hbm)$',symbols,re.M)
assert re.search(r'All (?:the )?simulator processes exited successfully',(run/'stdout.log').read_text()+(run/'run.log').read_text())
assert r['commit_calls']==1 and r['query_calls']==(art/'path_nodes.raw').stat().st_size//4
expected_revision=meta['revision']+1
trace=[tuple(map(int,v)) for v in re.findall(r'native commit op=(\d+) status=(\d+) revision=(\d+)',(run/'run.log').read_text())]
assert trace==[(3,0,expected_revision)]+[(7,0,expected_revision)]*r['query_calls']
report=dict(status='passed',result=r,artifact_hashes=hashes,
 scope='Actual three-bank seed/search/commit/query CUs on full native graph with shared authority; search artifacts byte-identical to C-model, publication separately audited',
 limitations=['One immutable serialized snapshot','Initial authority imported from audited C-model state','No full cohort, asynchronous protocol or board result'],board_result=False)
(run/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status='passed',result=r)))
