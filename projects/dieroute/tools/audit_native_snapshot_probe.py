"""Audit completed native whole-search C-model differential execution evidence."""
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from select_native_cross_die_snapshot import select

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):
            h.update(b)
    return h.hexdigest()

run = Path(sys.argv[1])
m = json.loads((run/'manifest.json').read_text())
assert m['returncode'] == 0 and m['inputs_unchanged']
r = json.loads((run/'stdout.log').read_text())
assert r == m['result'] and r['status'] == 'passed'
for path, expected in m['source_hashes'].items():
    assert sha(Path(path)) == expected
snap = Path(m['command'][3])
a = json.loads((snap/'independent_audit.json').read_text())
assert a['status'] == 'passed'
for path, expected in a['hashes'].items():
    # Exporter source can evolve after this completed export; its historic hash
    # is provenance, while all authority payloads must still match exactly.
    if Path(path).parent == snap:
        assert sha(Path(path)) == expected
meta = json.loads((snap/'snapshot.json').read_text())
assert (int(m['command'][5]),int(m['command'][6])) == (meta['net_id'],meta['sink'])
if (snap/'selection.json').exists():
    selection = json.loads((snap/'selection.json').read_text())
    assert selection == select(Path(m['command'][2]).parent)
    assert selection['sequence'] == meta['proposal_sequence']
    assert selection['net'] == meta['net_id'] and selection['sink'] == meta['sink']
    assert not (selection['source_mask'] & selection['sink_mask'])
log = (run/'run.log').read_text()
matches = re.findall(r'^reference complete expanded=(\d+) reads=(\d+)$',log,re.M)
assert matches == [(str(r['expanded']),str(r['observations']))]
symbols = subprocess.check_output(['nm','--defined-only',str(run/'probe')],text=True)
assert re.search(r'\bT dieroute_native_snapshot_search_hbm$',symbols,re.M)
assert r['search_status'] in (0,1,2,3)
report = dict(status='passed',verified_ns=time.time_ns(),result=r,
    hashes={str(p):sha(p) for p in (run/'manifest.json',run/'probe',run/'stdout.log',run/'run.log')},
    scope='Native actual-top C-model execution with independent dictionary resource costs and internal exact path/ordered-read assertions; auditor checks provenance and completion, does not independently replay exported paths',
    limitations=['Single immutable snapshot and worker','Path and observation comparisons are executable assertions; individual paths are not exported','No RTL, physical implementation, board or concurrent protocol result'],
    board_result=False,research_complete=False)
(run/'independent_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status='passed',result=r)))
