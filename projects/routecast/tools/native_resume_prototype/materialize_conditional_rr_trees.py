"""Private full-route materialization and original-native FULL/STA of conditioned trees."""
import json,re,shutil,subprocess,os,sys,time
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_route_ledger_import_compact import physical_paths
from serialize_live_native_candidate import serialize
from stream_native_route_audit_cached import audit
from freeze_priority_family import closure
ROOT=Path(__file__).resolve().parents[2];w,i=map(int,sys.argv[1:]);prior=ROOT/f'experiments/native_resume_conditional_rr_floors_w{w}_m{i}_2026-10-07';r=json.loads((prior/'receipt.json').read_text());proof=json.loads((prior/'verification.json').read_text());assert proof['receipt_sha256']==sha(prior/'receipt.json') and not proof['simultaneous_replacement_overflow'];p=json.loads((prior/'protocol.json').read_text());assert r['protocol_sha256']==sha(prior/'protocol.json') and all(sha(f)==h for f,h in p['inputs'].items())
base=ROOT/f'experiments/native_resume_singlepass_floor_w{w}_m{i}_workflow_2026-10-07';native=json.loads((base/'receipt.json').read_text());source=base/'canonical';out=ROOT/f'experiments/native_resume_conditional_materialized_w{w}_m{i}_2026-10-07';out.mkdir(exist_ok=False);start=time.perf_counter();ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';meta=json.loads(ep.read_text());graph,digest,nodes,f,rc,queries=load_endpoints(ep);paths=physical_paths(source/'design.route');slot_by_arc={(u,f['dest_ranks'][s],f['switch_ids'][s]):s for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};changed={x['query']['connection_id']:x['physical_edge_ids'] for row in r['rows'] for x in row['records']};records=[]
for q in queries:
 cid=q['connection_id'];name=meta['net_names'][str(q['net_id'])]
 if cid in changed:edges=changed[cid]
 else:
  ps=[p for p in paths[name] if p[0][0]==q['source'] and p[-1][0]==q['sink']];assert len(ps)==1;old=ps[0];edges=[f['edge_ids'][slot_by_arc[u,v,switch]] for (u,_),(v,switch) in zip(old,old[1:])]
 records.append(dict(q,answer=dict(physical_edge_ids=edges)))
for file in ('design.blif','design.net','design.place'):shutil.copyfile(source/file,out/file)
text,bindings=serialize(dict(records=records),ep,source/'identity.jsonl',out/'design.place');(out/'design.route').write_text(text)
actual=physical_paths(out/'design.route');assert len(bindings)==len(queries)
expected_paths={name:Counter(ps) for name,ps in paths.items() if ps};edges={eid:(u,f['dest_ranks'][s],f['switch_ids'][s]) for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])}
for row in r['rows']:
 expected_paths[row['net']]=Counter()
 for record in row['records']:
  q=record['query'];path=[(q['source'],None)]
  for eid in record['physical_edge_ids']:u,v,switch=edges[eid];assert u==path[-1][0];path.append((v,switch))
  expected_paths[row['net']][tuple(path)]+=1
assert {name:Counter(ps) for name,ps in actual.items() if ps}==expected_paths
cmd=native['canonical']['command'];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};inputs={str(file):sha(file) for file in (prior/'receipt.json',prior/'verification.json',base/'receipt.json',source/'design.route',source/'identity.jsonl',ep,graph,Path(cmd[0]))};inputs.update({str(source/file):sha(source/file) for file in ('design.blif','design.net','design.place')})
protocol=dict(inputs=inputs,sources=closure([Path(__file__)]),command=cmd,selected_net_names=p['selected_net_names'],scope='Materialize all three own-worst-path NET replacements simultaneously from independently conditioned trees; other NET physical paths unchanged. One native analysis attempt, no QoR/cold-driven selection. Prior candidate/conditional-query acquisition costs excluded.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');built=time.perf_counter()
with (out/'native.log').open('w') as stream:code=subprocess.run(cmd,cwd=out,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
log=(out/'native.log').read_text();native_seconds=time.perf_counter()-built
cp=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log);wire=re.findall(r'Total wirelength:\s*(\d+)',log);mis=re.findall(r'Found (\d+) mismatches',log);fix=re.findall(r'Fixed (\d+) routing traces',log)
result=dict(protocol_sha256=sha(out/'protocol.json'),exit_code=code,cpd_ns=cp[-1] if cp else None,wirelength=int(wire[-1]) if wire else None,mismatches=int(mis[-1]) if mis else None,fixups=int(fix[-1]) if fix else None,construction_seconds=built-start,native_analysis_seconds=native_seconds,all_untouched_net_paths_preserved=True,scope=protocol['scope'])
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');assert code==0 and 'VPR succeeded' in log and result['mismatches']==result['fixups']==0
physical=audit(graph,out/'design.route');assert physical['overflow_units']==0 and len(physical['connections'])==len(queries)
observed=Counter((name,path[0][0],path[-1][0]) for name,ps in actual.items() for path in ps);target=Counter((meta['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in queries);assert observed==target
assert all(sha(file)==h for file,h in {**inputs,**protocol['sources']}.items());assert physical_paths(out/'design.route')==actual
result.update(physical_audit=physical,all_endpoints_match=True,total_materialization_analysis_proof_seconds=time.perf_counter()-start,files={str(file):sha(file) for file in out.iterdir() if file.is_file() and file.name!='receipt.json'})
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(w,result['cpd_ns'],result['wirelength'],result['total_materialization_analysis_proof_seconds'],flush=True)
