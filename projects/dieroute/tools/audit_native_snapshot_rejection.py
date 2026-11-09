"""Audit negative native path commits and equality to clean successful replay."""
import hashlib
import json
import struct
import sys
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return h.hexdigest()

run,baseline=map(Path,sys.argv[1:3])
m=json.loads((run/'manifest.json').read_text())
assert m['returncode']==0 and m['inputs_unchanged']
for p,h in m['source_hashes'].items():assert sha(Path(p))==h
r=json.loads((run/'stdout.log').read_text())
assert r==m['result'] and r['status']=='passed' and r['atomic_rejections']==2 and r['commit_calls']==3
authority=run/'authority'
rejected=list(struct.iter_unpack('<8Q',(authority/'rejected_completions.raw').read_bytes()))
assert len(rejected)==2 and rejected[0][0]==4 and rejected[0][3]>0 and rejected[1][0]==5
assert json.loads((baseline/'independent_audit.json').read_text())['status']=='passed'
hashes={}
for name in ('resources.raw','trees.raw','nets.raw','control.raw','canonical_reads.raw','proposal_completion.raw'):
    h=sha(authority/name)
    assert h==sha(baseline/name),name
    hashes[name]=h
report=dict(status='passed',result=r,authority_hashes=hashes,
    scope='Injected version mismatch and invalid PIP rejected with full authority byte assertions; corrected replay byte-equal to independently audited clean native commit',
    limitations=['Injected faults, not concurrent stale-state generation','C-model only; no DMA, RTL or board result'],board_result=False)
(run/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status='passed',atomic_rejections=2)))
