"""Same-window full transaction driver ABBA; native routing not timed here."""
import json,os,time,subprocess,shutil
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/dependency_cache_transaction_abba_2026-10-06';out.mkdir();(out/'sources').mkdir()
drivers={'live':'run_prepared_uncached_rc_move_sequence.py','prepared':'run_prepared_integer_rc_move_sequence.py'}
for n in ('benchmark_dependency_cache_transaction_abba.py',*drivers.values()):shutil.copyfile(root/'tools'/n,out/'sources'/n)
protocol={'order':['live','prepared','prepared','live'],'sources_sha256':{p.name:sha(p) for p in (out/'sources').iterdir()},'scope':'Fresh subprocess entire three-move transaction driver charged, including context loading/authentication, repair, search/trace/delta/cache, gates, XML audit, export. No faults. Both same accepted initial prediction and empty dependency cache. Both use same pinned prepared integer lattice; generation excluded and archived. Live means uncached plain search, prepared means dependency cache plus tracing. Native routing excluded from both; no overall routing net benefit claim.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');runs=[]
for trial,mode in enumerate(protocol['order']):
 fresh=root/f'experiments/dependency_cache_transaction_abba_fresh_{trial}_2026-10-06';env=dict(os.environ,PYTHONPATH=str(root/'tools'),ROUTECAST_TRANSACTION_OUTPUT=str(fresh));env.pop('ROUTECAST_INJECT_FAILURES',None);start=time.perf_counter()
 with (out/f'{trial}_{mode}.log').open('w') as log:code=subprocess.run(['python3',str(root/'tools'/drivers[mode])],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
 elapsed=time.perf_counter()-start;assert code==0;fr=json.loads((fresh/'receipt.json').read_text());assert all(not x['failure_phases'] for x in fr['steps']);assert [x['cache_hits'] for x in fr['steps']]==([0,0,0] if mode=='live' else [0,7,31]);assert all(sha(Path(n))==h for n,h in fr['inputs_sha256'].items());assert all(sha(fresh/'sources'/n)==h for n,h in fr['sources_sha256'].items())
 reference=root/'experiments/adder_tree_transactional_rc_moves_2026-10-06'
 for step in range(1,4):
  for kind in ('journal','physical'):assert (fresh/f'step_{step}_{kind}.json').read_bytes()==(reference/f'step_{step}_{kind}.json').read_bytes()
  assert json.loads((fresh/f'step_{step}_prediction.json').read_text())==json.loads((reference/f'step_{step}_prediction.json').read_text());assert (fresh/f'step_{step}.pressure').read_bytes()==(reference/f'step_{step}.pressure').read_bytes()
 row={'trial':trial,'mode':mode,'full_driver_s':elapsed,'fresh_output':str(fresh),'fresh_receipt_sha256':sha(fresh/'receipt.json'),'log_sha256':sha(out/f'{trial}_{mode}.log')};runs.append(row);print({'trial':trial,'mode':mode,'full_driver_s':elapsed},flush=True)
assert all(sha(root/'tools'/n)==h for n,h in protocol['sources_sha256'].items())
a=sum(x['full_driver_s'] for x in runs if x['mode']=='live')/2;b=sum(x['full_driver_s'] for x in runs if x['mode']=='prepared')/2
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'runs':runs,'live_mean_s':a,'prepared_mean_s':b,'prepared_over_live':b/a,'all_prediction_and_journal_audit_pressure_equal_reference':True},indent=2)+'\n');print(a,b,b/a)
