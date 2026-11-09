"""Independent prepared-CSR/electrical replay against original XML path budgets."""
import json,shutil,time
from pathlib import Path
from array import array
from fractions import Fraction
from prepared_csr import read,U64
from buffered_rc_context import load
from buffered_rc_node_classes import arc_delay
from pre_route_endpoints import sha

def run():
 base=Path('experiments');parent=base/'conv_layer_length_switch_prediction_v2_2026-10-06';budget=base/'conv_layer_channel_frontier_exact_budgets_2026-10-06';context=base/'conv_layer_exact_buffered_rc_classes_2026-10-06';frontier=base/'conv_layer_channel_conflict_frontier_v2_2026-10-06/report.json';csr=base/'conv_layer_length_switch_csr_2026-10-06/csr'
 pp=json.loads((parent/'protocol.json').read_text());pr=json.loads((parent/'receipt.json').read_text());br=json.loads((budget/'receipt.json').read_text());bp=json.loads((budget/'protocol.json').read_text())
 assert br['protocol_sha256']==sha(budget/'protocol.json') and br['budgets_sha256']==sha(budget/'budgets.json')
 assert pr['protocol_sha256']==sha(parent/'protocol.json') and pr['prediction_sha256']==sha(parent/'prediction.json')
 assert all(sha(v['path'])==v['sha256'] for v in bp['inputs'].values()) and all(sha(p)==h for p,h in bp['selection_sha256'].items())
 graph=pp['inputs']['graph'];m,f=read(csr,graph['sha256']);assert sha(csr/'manifest.json')==pp['csr_manifest_sha256']
 ids,classes,switches=load(context,graph['sha256']);assert len(ids)==m['nodes']==873536
 slots=array('Q',[0])*m['edges']
 for slot,eid in enumerate(f['edge_ids']):slots[eid]=slot
 expected={r['connection_id']:Fraction(r['delay_seconds_numerator'],r['delay_seconds_denominator']) for r in json.loads((budget/'budgets.json').read_text())}
 selection=json.loads(frontier.read_text());assert set(expected)==set(selection['whole_net_connection_ids']) and len(expected)==75
 results=[]
 for row in json.loads((parent/'prediction.json').read_text())['connections']:
  cid=row['connection_id']
  if cid not in expected:continue
  node=row['source'];resistance,capacitance=classes[ids[node]];delay=resistance*capacitance/2
  for eid in row['physical_edge_ids']:
   slot=slots[eid];assert f['row_offsets'][node]<=slot<f['row_offsets'][node+1] and f['costs'][slot]!=U64
   node=f['dest_ranks'][slot];delay+=arc_delay(classes,switches,ids[node],f['switch_ids'][slot])
  assert node==row['sink'] and delay==expected[cid]
  results.append({'connection_id':cid,'numerator':delay.numerator,'denominator':delay.denominator})
 assert len(results)==75
 out=base/'conv_layer_frontier_budget_parity_2026-10-06';out.mkdir();(out/'source').mkdir()
 names=['check_conv_layer_frontier_budget_parity.py','prepared_csr.py','buffered_rc_context.py','buffered_rc_node_classes.py','pre_route_endpoints.py']
 for name in names:shutil.copyfile(Path('tools')/name,out/'source'/name)
 receipt={'connections':75,'all_original_xml_budgets_match_prepared_electrical_replay':True,'budget_receipt_sha256':sha(budget/'receipt.json'),'context_receipt_sha256':sha(context/'receipt.json'),'prediction_receipt_sha256':sha(parent/'receipt.json'),'csr_manifest_sha256':sha(csr/'manifest.json'),'source_sha256':{name:sha(out/'source'/name) for name in names},'scope':'exact original path-model parity; no native STA, branch load or accepted repair'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':run()
