"""Fail-closed comparison of complete, physically audited matched evaluations."""
import json,pathlib,hashlib,argparse
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
NAMES=['ordinary_additive_undriven_v2_authenticated_host_evaluation','ordinary_length_switch_undriven_v2_authenticated_host_evaluation']
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def load(name):
 p=BASE/name
 files={n:p/n for n in ('protocol.json','receipt.json','spatial_maps.json')}
 missing=[str(v) for v in files.values() if not v.is_file()]
 if missing:raise FileNotFoundError('incomplete evaluation: '+', '.join(missing))
 hashes={n:sha(v) for n,v in files.items()}
 protocol=json.loads(files['protocol.json'].read_text());receipt=json.loads(files['receipt.json'].read_text());completion_path=p/'completion.json'
 if name==NAMES[0]:
  completion=json.loads(completion_path.read_text())
  assert completion['receipt_sha256']==hashes['receipt.json']
  assert completion['stage_exit_code']==0 and completion['input_and_frozen_source_hashes_verified']
 else:
  chain=BASE/'length_switch_completion_chain'
  cr=json.loads((chain/'receipt.json').read_text());cp=json.loads((chain/'protocol.json').read_text())
  assert cr['protocol_sha256']==sha(chain/'protocol.json')
  assert len(cr['stages'])==2 and all(v['exit_code']==0 for v in cr['stages'])
  assert cr['stages'][1]['command']==['python3','-u','tools/evaluate_stereo_length_switch.py','--prediction','ordinary_length_switch_prediction_undriven_v2_authenticated_host']
  for n,h in cp['sources'].items():assert sha(chain/'source'/n)==h
  parent=pathlib.Path(protocol['inputs']['prediction']['path']).parent
  assert cp['parent_protocol_sha256']==sha(parent/'protocol.json')
  assert cr['prediction_receipt_sha256']==sha(parent/'receipt.json')
  assert sha(p/'source'/'evaluate_stereo_length_switch.py')==cp['sources']['evaluate_stereo_length_switch.py']
  hashes['chain_receipt.json']=sha(chain/'receipt.json')
 native=pathlib.Path(protocol['inputs']['native']['path']).parent
 nr=json.loads((native/'receipt.json').read_text());np=json.loads((native/'protocol.json').read_text())
 assert nr['protocol_sha256']==sha(native/'protocol.json') and nr['physical_checks_pass']
 assert nr['outputs']['physical_branches.json']==protocol['inputs']['native']['sha256']
 assert np['inputs']['graph']==protocol['inputs']['graph']
 assert all(sha(v['path'])==v['sha256'] for v in np['inputs'].values())
 hashes['native_audit_receipt.json']=sha(native/'receipt.json')
 assert receipt['protocol_sha256']==hashes['protocol.json']
 assert receipt['spatial_maps_sha256']==hashes['spatial_maps.json']
 assert receipt['inputs_unchanged'] and receipt['exact_full_cohort_match']
 assert receipt['reports']['requested_connections']==81610
 assert receipt['reports']['completed_connections']==81610
 assert receipt['reports']['failed_connections']==0
 for n,h in protocol['source_sha256'].items():assert sha(p/'source'/n)==h
 for v in protocol['inputs'].values():assert sha(v['path'])==v['sha256']
 physical=pathlib.Path(protocol['inputs']['prediction']['path']).parent
 physical=physical.parent/(physical.name+'_physical_audit')
 assert sha(physical/'receipt.json')==protocol['physical_audit_receipt_sha256']
 ar=json.loads((physical/'receipt.json').read_text())
 assert ar['protocol_sha256']==sha(physical/'protocol.json')
 assert ar['result']['all_physical_and_union_checks_passed']
 assert ar['result']['requested']==ar['result']['completed']==81610
 parent=pathlib.Path(protocol['inputs']['prediction']['path']).parent
 pr=json.loads((parent/'receipt.json').read_text())
 assert ar['prediction_receipt_sha256']==sha(parent/'receipt.json')
 assert pr['prediction_sha256']==protocol['inputs']['prediction']['sha256']
 assert pr['protocol_sha256']==sha(parent/'protocol.json')
 assert pr['journal_sha256']==sha(parent/'net_results.jsonl')
 assert pr['connections']==81610 and pr['nets']==61314 and pr['failed']==0
 return protocol,receipt,hashes

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check-ready',action='store_true');args=parser.parse_args()
 if args.check_ready:
  missing=[str(BASE/n/f) for n in NAMES for f in ('protocol.json','receipt.json','spatial_maps.json') if not (BASE/n/f).is_file()]
  required=[BASE/NAMES[0]/'completion.json',BASE/'length_switch_completion_chain'/'receipt.json']
  missing.extend(str(p) for p in required if not p.is_file())
  print(json.dumps({'artifacts_present':not missing,'missing':missing,'scope':'presence check only; full authentication occurs in comparison'}));return
 data=[load(n) for n in NAMES];a,b=data
 for k in ('graph','endpoints','native','alignment'):assert a[0]['inputs'][k]==b[0]['inputs'][k]
 assert a[0]['metrics']==b[0]['metrics'] and a[0]['revision_provenance']==b[0]['revision_provenance']
 for k in ('prediction_metrics.py','stream_metric_domain.py','pre_route_endpoints.py'):assert a[0]['source_sha256'][k]==b[0]['source_sha256'][k]
 assert a[1]['node_type_counts']==b[1]['node_type_counts']
 differences={}
 for domain in ('resource','spatial'):
  av,bv=a[1]['reports'][domain],b[1]['reports'][domain]
  for k in ('k','universe_size','nonzero_truth','top_k_tie_rule','truth_k_boundary'):assert av[k]==bv[k]
  differences[domain]={k:{'rc':av[k],'length_switch':bv[k],'rc_minus_length_switch':av[k]-bv[k]} for k in ('spearman','precision_at_k','recall_at_k','mae')}
 report={'evaluation_hashes':{n:d[2] for n,d in zip(NAMES,data)},'differences':differences,'overflow':{n:d[1]['reports']['prediction_overflow_units'] for n,d in zip(NAMES,data)},'source_sha256':sha(pathlib.Path(__file__)),'scope':'matched revised-frontend retrospective model comparison only; no unseen-family, legal feedback, hardware speedup, or end-to-end net-benefit claim'}
 out=BASE/'matched_host_model_comparison';out.mkdir(exist_ok=False);(out/'source').mkdir()
 (out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
