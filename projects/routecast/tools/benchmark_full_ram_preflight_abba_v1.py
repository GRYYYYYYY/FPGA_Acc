"""Matched compiler full 5794-query ABBA, startup/I/O included per arm."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
from prepared_csr import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_preflight_abba_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_ram_length_switch_prediction_v1_2026-10-09';build=R/'build/full_ram_preflight_matched_v1_2026-10-09';provenance=json.loads((build/'provenance.json').read_text())
for p,h in provenance['bindings'].items():assert sha(p)==h
reference=[json.loads(line) for line in (B/'net_results.jsonl').read_text().splitlines()];assert len(reference)==5794
r=json.loads((B/'receipt.json').read_text());assert r['status']=='COMPLETE_AUDITED_PREDICTION'
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
m,f=read(B/'csr',json.loads((B/'prediction.json').read_text())['physical_graph_sha256']);del f
input_text=''.join(' '.join(map(str,[x['source'],*sorted(map(int,x['result']['paths']))]))+'\n' for x in reference)
(D/'queries.txt').write_text(input_text)
paths=[Path(__file__),build/'provenance.json',build/'A',build/'B',B/'receipt.json',B/'net_results.jsonl',B/'csr/manifest.json',D/'queries.txt'];bindings={str(p):sha(p) for p in paths}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,order=['A','B','B','A'],queries=5794,connections=16819,timeout_each_s=600,compiler_flags=provenance['commands'],scope='Same O2 compiler/CSR/full query set; each fresh process includes payload loading/startup/output writes. Reused CSR construction excluded and charged separately; independent correctness checks after timing. Host preflight mechanism only, not native end-to-end or unseen-family evidence.'),indent=2)+'\n')
rows=[]
for arm,label in enumerate(('A','B','B','A')):
 out=D/f'arm_{arm}_{label}.jsonl';t=time.perf_counter()
 with (D/'queries.txt').open('r') as inp,out.open('x') as stdout,(D/f'arm_{arm}.stderr').open('x') as err:
  try:code=subprocess.run([str(build/label),str(B/'csr'),'--batch'],stdin=inp,stdout=stdout,stderr=err,timeout=600).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 elapsed=time.perf_counter()-t;t=time.perf_counter();actual=[json.loads(x) for x in out.read_text().splitlines()];equal=len(actual)==len(reference) and all(a==b['result'] for a,b in zip(actual,reference));verify_s=time.perf_counter()-t
 row=dict(arm=arm,label=label,exit_code=code,process_startup_query_output_s=elapsed,verification_s=verify_s,completed_queries=len(actual),all_paths_and_counters_equal=equal,output_sha256=sha(out));rows.append(row);(D/f'arm_{arm}_receipt.json').write_text(json.dumps(row,indent=2)+'\n');print(row,flush=True)
assert all(sha(p)==h for p,h in bindings.items())
passed=all(x['exit_code']==0 and x['all_paths_and_counters_equal'] for x in rows)
means={label:sum(x['process_startup_query_output_s'] for x in rows if x['label']==label)/2 for label in ('A','B')}
(D/'receipt.json').write_text(json.dumps(dict(passed=passed,rows=rows,mean_s=means,B_over_A=means['B']/means['A'],bindings=bindings,scope='Four descriptive matched host process measurements; no broad confidence interval, native quality or end-to-end benefit.'),indent=2)+'\n');print('passed',passed,means,flush=True)
