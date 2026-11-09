"""Bind the archived type decomposition to authenticated full evaluation/audit."""
import json,pathlib,hashlib
from compare_stereo_matched_evaluations import load,NAMES,BASE

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 protocol,receipt,hashes=load(NAMES[0])
 out=BASE/'full_occupancy_type_diagnosis';report=json.loads((out/'report.json').read_text())
 assert report['source_sha256']==sha(out/'source/stereo_occupancy_type_diagnosis.py')
 assert report['prediction_sha256']==protocol['inputs']['prediction']['sha256']
 assert report['native_sha256']==protocol['inputs']['native']['sha256']
 parent=pathlib.Path(protocol['inputs']['prediction']['path']).parent
 prediction_protocol=json.loads((parent/'protocol.json').read_text())
 assert report['manifest_sha256']==prediction_protocol['csr_manifest_sha256']
 physical=parent.parent/(parent.name+'_physical_audit')
 ar=json.loads((physical/'receipt.json').read_text())['result']
 pred=report['reports']['prediction'];native=report['reports']['native']
 for label,rows in [('prediction',pred),('native',native)]:
  assert set(rows)=={'SOURCE','SINK','OPIN','IPIN','CHANX','CHANY'}
  assert sum(v['overflow_units'] for v in rows.values())==receipt['reports'][label+'_overflow_units']
  assert all(0<=v['overused_nodes']<=v['occupied_nodes']<=receipt['node_type_counts'][k] for k,v in rows.items())
 assert sum(v['occupied_nodes'] for v in pred.values())==ar['occupied_nodes']
 assert sum(v['net_node_touches'] for v in pred.values())==ar['net_node_touches']
 assert sum(pred[k]['overflow_units'] for k in ('CHANX','CHANY'))==ar['predicted_channel_overuse_units']
 assert pred['SOURCE']['net_node_touches']==61314 and pred['SINK']['net_node_touches']==81610
 assert pred['SOURCE']==native['SOURCE'] and pred['SINK']==native['SINK']
 result={'report_sha256':sha(out/'report.json'),'checker_sha256':sha(pathlib.Path(__file__)),'evaluation_sha256':hashes,'physical_receipt_sha256':protocol['physical_audit_receipt_sha256'],'all_receipt_bindings_and_aggregate_checks_pass':True,'pin_overflow_units':sum(pred[k]['overflow_units'] for k in ('OPIN','IPIN')),'pin_overflow_fraction':sum(pred[k]['overflow_units'] for k in ('OPIN','IPIN'))/ar['all_type_overuse_units'],'scope':'authenticated descriptive decomposition; no independent original-XML recomputation or causal claim'}
 (out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 (out/'completion.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
