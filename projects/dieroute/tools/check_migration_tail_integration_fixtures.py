"""Reuse frozen tail oracles against the isolated migration/tail combination."""
import hashlib,json,subprocess
from pathlib import Path

D=Path('work/rr_migration_remaining_tail_integration_20261016').resolve()
parent=Path('work/rr_remaining_layer_tail_variant_20261015').resolve()
O=D/'tail_fixture_checks';O.mkdir(exist_ok=False);records=[];inputs=[D/'source_manifest.json',D/'build/libdieroute_rr_backend.a',Path(__file__)]
for name in ['oracle','multilayer','alias','counterexample']:
    source=parent/(name+'_check.cpp');binary=O/name;inputs.append(source)
    command=['c++','-std=c++17','-O2','-I'+str(D/'source/dieroute/include'),'-I'+str(D/'source/persistroute/include'),str(source),str(D/'build/libdieroute_rr_backend.a'),'-pthread','-o',str(binary)]
    with (O/(name+'.compile.log')).open('x') as stream:rc=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT).returncode
    assert rc==0,(name,rc)
    with (O/(name+'.stdout')).open('x') as stdout,(O/(name+'.stderr')).open('x') as stderr:rc=subprocess.run([str(binary)],stdout=stdout,stderr=stderr).returncode
    assert rc==0,(name,rc)
    expected=parent/(name+'.stdout');assert (O/(name+'.stdout')).read_bytes()==expected.read_bytes(),name
    inputs.extend([expected,binary,O/(name+'.stdout')]);records.append(dict(name=name,returncode=rc,output_matches_parent=True))
report=dict(status='combined_backend_enabled_tail_matches_four_frozen_oracle_fixtures',checks=records,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},scope='Enabled-tail oracle, bounded comparisons, membership aliases and known counterexample on combined backend. No migrated enabled-tail host run or full native result.',research_complete=False)
(O/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(records))
