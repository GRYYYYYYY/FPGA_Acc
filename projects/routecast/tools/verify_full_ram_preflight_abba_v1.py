"""Independent four-arm complete output and matched-configuration audit."""
import json,math
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'full_ram_preflight_abba_v1_2026-10-09';D=E/'full_ram_preflight_abba_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
r=json.loads((B/'receipt.json').read_text());assert r['passed'];p=json.loads((B/'protocol.json').read_text());assert p['order']==['A','B','B','A'] and p['queries']==5794 and p['connections']==16819
for file in (r,p):
 for path,digest in file['bindings'].items():assert sha(path)==digest
build=R/'build/full_ram_preflight_matched_v1_2026-10-09';provenance=json.loads((build/'provenance.json').read_text());commands=provenance['commands'];assert len(commands)==2 and commands[0][:4]==commands[1][:4]==['/usr/bin/g++','-std=c++17','-O2','-Iinclude']
for path,digest in provenance['bindings'].items():assert sha(path)==digest
ref=[json.loads(x) for x in (E/'full_ram_length_switch_prediction_v1_2026-10-09/net_results.jsonl').read_text().splitlines()];assert len(ref)==5794
expected_queries=[(x['source'],*sorted(map(int,x['result']['paths']))) for x in ref];queries=[tuple(map(int,line.split())) for line in (B/'queries.txt').read_text().splitlines()];assert queries==expected_queries
assert sum(len(x['result']['paths']) for x in ref)==16819
rows=[];paths=[Path(__file__),B/'protocol.json',B/'receipt.json',build/'provenance.json',B/'queries.txt']
for i,label in enumerate(('A','B','B','A')):
 armfile=B/f'arm_{i}_receipt.json';arm=json.loads(armfile.read_text());outfile=B/f'arm_{i}_{label}.jsonl';assert arm['arm']==i and arm['label']==label and arm['exit_code']==0 and sha(outfile)==arm['output_sha256']
 actual=[json.loads(x) for x in outfile.read_text().splitlines()];assert len(actual)==5794
 for a,b in zip(actual,ref):assert a==b['result']
 assert arm==r['rows'][i];rows.append(arm);paths.extend([armfile,outfile])
means={label:math.fsum(x['process_startup_query_output_s'] for x in rows if x['label']==label)/2 for label in ('A','B')}
assert means==r['mean_s'] and abs(means['B']/means['A']-r['B_over_A'])<1e-14
out=dict(passed=True,arms=4,queries_per_arm=5794,connection_paths_per_arm=16819,all_outputs_and_counters_exact=True,mean_s=means,B_over_A=means['B']/means['A'],bindings={str(x):sha(x) for x in paths},scope='Independent all-line comparison and compiler/inputs/order/mean arithmetic. Four sequential host measurements only; no variance-based generalization, HLS or native end-to-end benefit.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
