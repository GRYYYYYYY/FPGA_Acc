"""Bind fresh transaction outputs to actual audited native route hashes."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'transactional_rc_native_pipeline_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert sha(out/'protocol.json')==r['protocol_sha256'];assert all(sha(root/'tools'/n)==h for n,h in p['source_sha256'].items());assert all(sha(v['path'])==v['sha256'] for v in p['inputs'].values())
prior=base/'native_pressure_transactional_rc_moves_2026-10-06';native=json.loads((prior/'receipt.json').read_text());verified=json.loads((prior/'verification.json').read_text());assert sha(prior/'receipt.json')==verified['receipt_sha256'];records=[]
for run in r['runs']:
 assert run['driver_s']+sum(x['native_s'] for x in run['native'])<=run['full_prepared_pipeline_s']
 if run['mode']=='on':
  fresh=Path(run['fresh_output']);fr=json.loads((fresh/'receipt.json').read_text());assert all(sha(Path(n))==h for n,h in fr['inputs_sha256'].items());assert all(sha(fresh/'sources'/n)==h for n,h in fr['sources_sha256'].items())
  for step in fr['steps']:
   k=step['step'];assert not step['failure_phases'];assert (fresh/f'step_{k}_prediction.json').read_bytes()==(base/'adder_tree_transactional_rc_moves_2026-10-06'/f'step_{k}_prediction.json').read_bytes();assert (fresh/f'step_{k}.pressure').read_bytes()==(base/'adder_tree_transactional_rc_moves_2026-10-06'/f'step_{k}.pressure').read_bytes()
  run['fresh_receipt_sha256']=sha(fresh/'receipt.json')
 for case in run['native']:
  route=Path(case['route_path']);log=Path(case['log_path']);truth=next(x for x in native['results'] if x['step']==case['step'] and x['mode']==run['mode']);assert sha(route)==truth['route_sha256'];assert sha(prior/f"{case['step']:02d}_{truth['trial']}_{truth['mode']}_physical.json")==truth['physical_sha256'];text=log.read_text();assert 'VPR succeeded' in text
  if run['mode']=='on':assert 'RouteCast pressure applied: 2 channel nodes' in text
  else:assert 'RouteCast pressure applied' not in text
  case['actual_route_sha256']=sha(route);case['actual_log_sha256']=sha(log);case['prior_physical_audit_sha256']=truth['physical_sha256']
 records.append(run)
off=sum(x['full_prepared_pipeline_s'] for x in records if x['mode']=='off')/2;on=sum(x['full_prepared_pipeline_s'] for x in records if x['mode']=='on')/2
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'runs':records,'off_mean_s':off,'on_mean_s':on,'on_over_off':on/off,'all_actual_routes_match_independently_xml_audited_prior':True,'scope':'Prepared three-move cohort; on driver loading/authentication, repair/search/transaction/validation/XML audit/output charged, off native-only. Same fixed placement routes, initial accepted prediction generation excluded. Single ABBA, no steady-state timing generalization/native tree reuse.'},indent=2)+'\n');print(off,on,on/off)
