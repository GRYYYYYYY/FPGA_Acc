#!/usr/bin/env python3
"""Exercise cache corruption rejection on disposable copies of a real bundle."""
import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

from run_development import ROOT, sha
from validate_candidate import read_state


def check(bundle, candidate, output):
    if output.exists():
        raise ValueError('output already exists')
    output.mkdir(parents=True)
    source_sha = sha(bundle/'rr_export.sqlite')
    candidate_sha = sha(candidate)
    state = read_state(candidate)
    node = state[1][0]['source']
    pair = (node, state[1][0]['path'][0])
    cases = {'checksum': 'changed bound input/source',
             'identity': 'RR cache identity/coverage metadata mismatch',
             'node': 'RR cache missing used nodes', 'edge': 'RR cache missing used edges',
             'ambiguity': 'ambiguous physical switch identity'}
    results = []
    for case, message in cases.items():
        root = output/case; root.mkdir()
        copied = root/'bundle';shutil.copytree(bundle,copied)
        manifest = json.loads((copied/'manifest.json').read_text())
        for name, entry in manifest['files'].items():
            entry['path'] = str(copied/name)
        database = copied/'rr_export.sqlite';database.chmod(0o644)
        if case == 'checksum':
            with database.open('ab') as stream:
                stream.write(b'damaged')
        else:
            with sqlite3.connect(database) as db:
                if case == 'identity':
                    meta = json.loads(db.execute('SELECT value FROM metadata WHERE key=?',('manifest',)).fetchone()[0])
                    meta['bindings']['rr_graph']['sha256'] = '0'*64
                    db.execute('UPDATE metadata SET value=? WHERE key=?',(json.dumps(meta),'manifest'))
                elif case == 'node':
                    db.execute('DELETE FROM nodes WHERE id=?',(node,))
                elif case == 'edge':
                    db.execute('DELETE FROM edges WHERE src=? AND dst=?',pair)
                else:
                    switch = db.execute('SELECT switch_id FROM edges WHERE src=? AND dst=?',pair).fetchone()[0]
                    db.execute('UPDATE edges SET alternatives=? WHERE src=? AND dst=?',
                               (json.dumps([switch,switch+1]),*pair))
            # Deliberately let checksum validation pass to test structural
            # rejection separately from simple file-integrity rejection.
            manifest['files']['rr_export.sqlite']['sha256'] = sha(database)
        (copied/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        work=root/'validation';work.mkdir();shutil.copyfile(candidate,work/'candidate.state')
        command=[sys.executable,str(ROOT/'tools/validate_candidate.py'),str(copied),str(work/'candidate.state'),str(work)]
        run=subprocess.run(command,capture_output=True,text=True)
        (root/'stdout.log').write_text(run.stdout);(root/'stderr.log').write_text(run.stderr)
        if run.returncode==0 or message not in run.stderr or (work/'validation.json').exists() or (work/'quality.txt').exists():
            raise ValueError('did not reject intended corruption: '+case)
        if sha(work/'candidate.state')!=candidate_sha or json.loads((work/'costs.json').read_text())['complete']:
            raise ValueError('failure changed candidate or reported completion')
        results.append({'case':case,'exit_status':run.returncode,'expected_error':message,
                        'stderr_sha256':sha(root/'stderr.log'),'candidate_unchanged':True,'native_gate_certificate_absent':True})
    if sha(bundle/'rr_export.sqlite')!=source_sha or sha(candidate)!=candidate_sha:
        raise ValueError('original inputs changed')
    result={'schema':'FUSIONPAR_RR_CACHE_NEGATIVE_CONTROLS_V1','pass':True,'cases':results,
            'original_bundle':{'path':str(bundle/'manifest.json'),'sha256':sha(bundle/'manifest.json')},
            'original_cache_sha256':source_sha,'candidate_sha256':candidate_sha,
            'checker_sha256':sha(__file__),'limits':['Disposable mutations; original successful artifacts unchanged']}
    (output/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bundle',type=Path,required=True)
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();check(a.bundle.resolve(),a.candidate.resolve(),a.output.resolve())
