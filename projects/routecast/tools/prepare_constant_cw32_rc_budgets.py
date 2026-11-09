"""Independent full XML exact PathRC parity for new-family baseline budgets."""
import json,subprocess,os,xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from pre_route_endpoints import sha
from path_rc import PathRC
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from prepared_csr import read

def main():
 root=Path(__file__).resolve().parents[1];summary=[]
 for i in range(1,7):
  name=f'mult_{i:03d}';subprocess.run(['python3',str(root/'tools/prepare_constant_cw32_buffered_rc_classes.py'),name],cwd=root,env=dict(os.environ,PYTHONPATH=str(root/'tools')),check=True,capture_output=True);context=root/'experiments/constant_multiplier_cw32_exact_buffered_rc_classes_2026-10-06'/name;baseline=root/'experiments/constant_multiplier_family_predictions_cw32_2026-10-06'/name/'sparse_reset';pr=json.loads((baseline/'receipt.json').read_text());assert sha(baseline/'prediction.json')==pr['prediction_sha256'];pred=json.loads((baseline/'prediction.json').read_text());p=json.loads((baseline/'protocol.json').read_text());graph=p['inputs']['graph'];wanted={e for r in pred['connections'] for e in r['physical_edge_ids']};nodes={};switches={};edges={};stack=[];eid=0
  for event,e in ET.iterparse(graph['path'],events=('start','end')):
   if event=='start':stack.append(e);continue
   tag=stack[-2].tag if len(stack)>1 else None
   if e.tag=='node' and tag=='rr_nodes':nodes[int(e.get('id'))]=SimpleNamespace(timing=dict(e.find('timing').attrib))
   if e.tag=='switch' and tag=='switches':switches[int(e.get('id'))]=ET.tostring(e,encoding='unicode')
   if e.tag=='edge' and tag=='rr_edges':
    if eid in wanted:edges[eid]=SimpleNamespace(source=int(e.get('src_node')),sink=int(e.get('sink_node')),switch_id=int(e.get('switch_id')))
    eid+=1
   if tag in ('rr_nodes','rr_edges','switches','segments','block_types','grid','channels'):stack[-2].remove(e);e.clear()
   stack.pop()
  class Selected:
   def __len__(self):return eid
   def __getitem__(self,n):return edges[n]
  assert set(edges)==wanted;oracle=PathRC(SimpleNamespace(nodes=nodes,switches=switches,edges=Selected()));m,f=read(root/'experiments/constant_multiplier_family_length_switch_csr_cw32_2026-10-06'/name/'csr',graph['sha256']);rc=ExactBufferedRC(f,*load(context,graph['sha256']));budgets=[]
  for r in pred['connections']:
   independent=oracle.path(r['source'],r['physical_edge_ids']).delay;delay=rc.path(r['source'],r['sink'],r['physical_edge_ids']);assert independent==delay;budgets.append({k:r[k] for k in ('connection_id','net_id','source','sink')}|{'exact_delay_s':[delay.numerator,delay.denominator]})
  assert sha(graph['path'])==graph['sha256'];(context/'baseline_budgets.json').write_text(json.dumps(budgets)+'\n');parity={'source_sha256':sha(__file__),'context_receipt_sha256':sha(context/'receipt.json'),'prediction_receipt_sha256':sha(baseline/'receipt.json'),'baseline_budgets_sha256':sha(context/'baseline_budgets.json'),'all_exact_rc_equal_independent_original_xml_oracle':True,'connections':len(budgets),'scope':'Exact connection expansion RC, SOURCE zero start, not tree branching STA.'};(context/'baseline_parity.json').write_text(json.dumps(parity,indent=2)+'\n');summary.append({'design':name,'connections':len(budgets),'parity_sha256':sha(context/'baseline_parity.json')});print(json.dumps(summary[-1]),flush=True)
 (root/'experiments/constant_multiplier_cw32_exact_buffered_rc_classes_2026-10-06/summary.json').write_text(json.dumps(summary,indent=2)+'\n')
if __name__=='__main__':main()
