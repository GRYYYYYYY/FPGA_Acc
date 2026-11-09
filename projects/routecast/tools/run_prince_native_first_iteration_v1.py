"""Frozen all9 one-iteration paid native baseline, expected congested exits retained."""
import json,subprocess,shutil,os,resource,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_native_first_iteration_trial_v1_2026-10-20'
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
def main():
 pp=E/'prince_native_first_iteration_design_v1_2026-10-20/protocol.json';p=json.loads(pp.read_text());assert all(sha(f)==h for f,h in p['bindings'].items());D.mkdir(exist_ok=False);rows=[];start=time.perf_counter();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 for j in p['jobs']:
  d=Path(j['directory']);d.mkdir(parents=True);tick=time.perf_counter()
  for name,src in j['staging'].items():shutil.copyfile(src,d/name);assert sha(src)==sha(d/name)
  with (d/'native.log').open('x') as log:code=subprocess.call(j['command'],cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
  native_seconds=time.perf_counter()-tick;row=dict(case=j['case'],native_exit_code=code,native_seconds=native_seconds,independent_tree_endpoint_audit_pass=False,eligible_legal_route=False)
  try:
   graph=Path(j['command'][j['command'].index('--read_rr_graph')+1]);physical=audit(graph,d/'output.route');ep=E/'prince_native_cohort_v1_2026-10-20'/j['case']/'pre_route_endpoints.json';meta=json.loads(ep.read_text());assert sha(graph)==meta['graph_sha256'];names={int(m[1]):m[2] for line in (d/'output.route').read_text().splitlines() if (m:=NET.match(line))};expected=Counter((meta['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in meta['connections']);observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in physical['connections']);assert observed==expected
   (d/'physical_audit.json').write_text(json.dumps(physical)+'\n');row.update(independent_tree_endpoint_audit_pass=True,connections=len(meta['connections']),overflow_units=physical['overflow_units'],graph_sha256=meta['graph_sha256'])
  except Exception as exc:row['audit_error']=repr(exc)
  row['paid_stage_seconds']=time.perf_counter()-tick;row['files']={str(f):sha(f) for f in d.iterdir() if f.is_file()};(d/'receipt.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row);(D/'progress.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n');print('NATIVE_FIRST_ITER',j['case'],code,row['independent_tree_endpoint_audit_pass'],row.get('overflow_units'),flush=True)
 assert all(sha(f)==h for f,h in p['bindings'].items());(D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings={str(pp):sha(pp),str(Path(__file__)):sha(__file__)},continuous_seconds=time.perf_counter()-start,scope='One native iteration paid search/import/physical branch and endpoint audit. Congested exits not legal labels, no full native/canonical gate, physical timing or full workflow gain.'),indent=2)+'\n')
if __name__=='__main__':main()
