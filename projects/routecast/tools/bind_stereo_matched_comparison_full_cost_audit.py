"""Bind matched metrics to complete original XML length-switch transport audit."""
import json,shutil
from pathlib import Path
from compare_stereo_matched_evaluations import BASE,NAMES,load,sha

def run():
 audit=BASE/'matched_length_switch_control_full_xml_audit';prepared=BASE/'matched_length_switch_control';comparison=BASE/'matched_host_model_comparison';chain=BASE/'matched_model_comparison_completion_chain'
 ar=json.loads((audit/'receipt.json').read_text());ap=json.loads((audit/'protocol.json').read_text());pr=json.loads((prepared/'receipt.json').read_text());report=json.loads((comparison/'report.json').read_text());cr=json.loads((chain/'receipt.json').read_text())
 assert ar['protocol_sha256']==sha(audit/'protocol.json')
 assert ar['parent_receipt_sha256']==sha(prepared/'receipt.json')==ap['parent_receipt_sha256']
 assert ar['all_node_metadata_and_edge_costs_match_original_xml'] and ar['nodes']==3593250 and ar['edges']==39165143
 assert pr['manifest_sha256']==sha(prepared/'csr/manifest.json') and pr['protocol_sha256']==sha(prepared/'protocol.json')
 assert all(sha(audit/'source'/n)==h for n,h in ap['source_sha256'].items())
 assert cr['protocol_sha256']==sha(chain/'protocol.json') and len(cr['stages'])==1 and cr['stages'][0]['exit_code']==0
 cp=json.loads((chain/'protocol.json').read_text())
 assert all(sha(chain/'source'/n)==h for n,h in cp['source_sha256'].items())
 assert report['source_sha256']==sha(chain/'source/compare_stereo_matched_evaluations.py')
 data=[load(name) for name in NAMES]
 for name,(p,r,h) in zip(NAMES,data):
  assert report['evaluation_hashes'][name]==h
  assert p['inputs']['graph']==ap['graph']
 control=Path(data[1][0]['inputs']['prediction']['path']).parent
 pp=json.loads((control/'protocol.json').read_text())
 assert pp['conversion_receipt_sha256']==ar['parent_receipt_sha256'] and pp['csr_manifest_sha256']==pr['manifest_sha256']
 out=BASE/'matched_comparison_full_cost_evidence';out.mkdir(exist_ok=False);(out/'source').mkdir()
 shutil.copyfile(__file__,out/'source'/Path(__file__).name)
 receipt={'full_cost_audit_receipt_sha256':sha(audit/'receipt.json'),'comparison_report_sha256':sha(comparison/'report.json'),'comparison_chain_receipt_sha256':sha(chain/'receipt.json'),'control_manifest_sha256':pr['manifest_sha256'],'source_sha256':sha(__file__),'all_bindings_pass':True,'scope':'complete graph/cost transport and physically audited matched retrospective metrics; no unseen-family, legal feedback, hardware or total-time benefit claim'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':run()
