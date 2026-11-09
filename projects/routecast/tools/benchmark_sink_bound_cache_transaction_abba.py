"""Charge fresh full drivers; identical pruned policy, cache on/off ABBA."""
import json,os,time,subprocess
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1]
out=root/'experiments/sink_bound_cache_transaction_abba_2026-10-06';out.mkdir()
drivers={'off':'run_prepared_sink_bound_rc_move_sequence.py','on':'run_cached_sink_bound_rc_move_sequence.py'}
sources={n:sha(root/'tools'/n) for n in (*drivers.values(),Path(__file__).name)}
protocol={'order':['off','on','on','off'],'sources_sha256':sources,'scope':'Fresh three-move driver loading/authentication/search/cache/audits/export charged. Same prepared integer lattice and certified sink bounds. Their offline preparation and native routing excluded. Empty initial cache; no faults or per-query oracle. One ABBA cohort, no overall native net benefit claim.'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');runs=[]
reference=root/'experiments/adder_tree_prepared_sink_bound_rc_transactions_2026-10-06'
for trial,mode in enumerate(protocol['order']):
 fresh=root/f'experiments/sink_bound_cache_abba_fresh_{trial}_2026-10-06'
 env=dict(os.environ,PYTHONPATH=str(root/'tools'),ROUTECAST_TRANSACTION_OUTPUT=str(fresh));env.pop('ROUTECAST_INJECT_FAILURES',None)
 start=time.perf_counter()
 with (out/f'{trial}_{mode}.log').open('w') as log:
  code=subprocess.run(['python3',str(root/'tools'/drivers[mode])],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
 elapsed=time.perf_counter()-start;assert code==0
 r=json.loads((fresh/'receipt.json').read_text());assert [x['cache_hits'] for x in r['steps']]==([0,193,239] if mode=='on' else [0,0,0]);assert all(not x['failure_phases'] for x in r['steps'])
 assert all(sha(Path(p))==h for p,h in r['inputs_sha256'].items());assert all(sha(fresh/'sources'/n)==h for n,h in r['sources_sha256'].items())
 for step in range(1,4):
  for kind in ('journal','physical'):assert (fresh/f'step_{step}_{kind}.json').read_bytes()==(reference/f'step_{step}_{kind}.json').read_bytes()
  assert json.loads((fresh/f'step_{step}_prediction.json').read_text())==json.loads((reference/f'step_{step}_prediction.json').read_text())
  assert (fresh/f'step_{step}.pressure').read_bytes()==(reference/f'step_{step}.pressure').read_bytes()
 row={'trial':trial,'mode':mode,'full_driver_s':elapsed,'fresh_output':str(fresh),'receipt_sha256':sha(fresh/'receipt.json'),'log_sha256':sha(out/f'{trial}_{mode}.log')};runs.append(row);print(row,flush=True)
assert all(sha(root/'tools'/n)==h for n,h in sources.items())
a=sum(x['full_driver_s'] for x in runs if x['mode']=='off')/2;b=sum(x['full_driver_s'] for x in runs if x['mode']=='on')/2
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'runs':runs,'off_mean_s':a,'on_mean_s':b,'on_over_off':b/a,'all_predictions_journals_physical_pressure_equal_reference':True},indent=2)+'\n');print(a,b,b/a)
