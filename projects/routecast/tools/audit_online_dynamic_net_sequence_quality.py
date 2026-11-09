"""Post-outcome exact-decimal path RC and scalar cost comparison, not STA."""
import json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from fractions import Fraction
from pre_route_endpoints import sha
from prepared_csr import read
from path_rc import PathRC
from streaming_rr_nodes import read as read_nodes


def main():
 root=Path(__file__).resolve().parents[1];parent=root/'experiments/adder_tree_online_dynamic_net_sequence_2026-10-06';out=root/'experiments/adder_tree_online_dynamic_net_quality_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('audit_online_dynamic_net_sequence_quality.py','path_rc.py','streaming_rr_nodes.py','prepared_csr.py','pre_route_endpoints.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 protocol={'parent_receipt_sha256':sha(parent/'receipt.json'),'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'initial_state':'SOURCE resistance=0, delay=0 for both models','scope':'Post-outcome paired path scalar and exact-decimal connection expansion RC comparison. No branching load, STA, prospective budget or native pin legality. All 2064 state-specific connections retained; same-placement constant predictor reference, not RC admission.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');summary=[]
 for case in json.loads((parent/'receipt.json').read_text())['steps']:
  step=case['step'];name=f'step_{step}';dest=out/name;dest.mkdir();newfile=parent/f'step_{step}_prediction.json';assert sha(newfile)==case['prediction_sha256'];new=json.loads(newfile.read_text());auditfile=parent/f'step_{step}_physical.json';assert sha(auditfile)==case['physical_sha256'];a=json.loads(auditfile.read_text());assert a['all_physical_and_union_checks_passed']
  if step==0:
   oldroot=root/'experiments/adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset';oldfile=oldroot/'prediction.json';oldr=json.loads((oldroot/'receipt.json').read_text());assert sha(oldfile)==oldr['prediction_sha256']
  else:
   oldroot=root/'experiments/adder_tree_2L032_move_sequence_audit_2026-10-06';oldfile=oldroot/f'step_{step}_prediction.json';oldr=json.loads((oldroot/'receipt.json').read_text())['steps'][step-1];assert sha(oldfile)==oldr['prediction_sha256']
  old=json.loads(oldfile.read_text());graph=json.loads((root/'experiments/adder_tree_2L032_move_sequence_2026-10-06/protocol.json').read_text())['inputs']['rr_graph'];fields,res,cap,switches,segments,digest=read_nodes(graph['path']);assert digest==graph['sha256']
  nodes={nid:SimpleNamespace(timing={'R':res[i],'C':cap[i]}) for i,nid in enumerate(fields['node_ids'])};wanted={eid for pred in (old,new) for r in pred['connections'] for eid in r['physical_edge_ids']};edges={};stack=[];eid=0
  for event,e in ET.iterparse(graph['path'],events=('start','end')):
   if event=='start':stack.append(e);continue
   tag=stack[-2].tag if len(stack)>1 else None
   if e.tag=='edge' and tag=='rr_edges':
    if eid in wanted:edges[eid]=SimpleNamespace(source=int(e.get('src_node')),sink=int(e.get('sink_node')),switch_id=int(e.get('switch_id')))
    eid+=1
   if tag in ('rr_nodes','rr_edges','switches','segments','block_types','grid','channels'):stack[-2].remove(e);e.clear()
   stack.pop()
  class SelectedEdges:
   def __len__(self):return eid
   def __getitem__(self,i):return edges[i]
  assert set(edges)==wanted;oracle=PathRC(SimpleNamespace(nodes=nodes,switches=switches,edges=SelectedEdges()));m,f=read(root/'experiments/adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr',digest);cost={e:f['costs'][i] for i,e in enumerate(f['edge_ids'])};olds={r['connection_id']:r for r in old['connections']};rows=[]
  for r in new['connections']:
   b=olds[r['connection_id']];assert all(r[k]==b[k] for k in ('net_id','source','sink'));od=oracle.path(b['source'],b['physical_edge_ids']).delay;nd=oracle.path(r['source'],r['physical_edge_ids']).delay;oc=sum(cost[e] for e in b['physical_edge_ids']);nc=sum(cost[e] for e in r['physical_edge_ids']);rows.append({'connection_id':r['connection_id'],'old_scalar':oc,'new_scalar':nc,'old_rc_s_exact':str(od),'new_rc_s_exact':str(nd),'rc_increase':nd>od,'scalar_increase':nc>oc})
  (dest/'connections.json').write_text(json.dumps(rows,indent=2)+'\n');topology=a.get('net_union_topology');report={'design':name,'connections':len(rows),'scalar_increased':sum(r['scalar_increase'] for r in rows),'rc_increased':sum(r['rc_increase'] for r in rows),'max_scalar_ratio':max(r['new_scalar']/r['old_scalar'] for r in rows),'topology':topology,'prediction_sha256':sha(newfile),'reference_prediction_sha256':sha(oldfile),'physical_audit_sha256':sha(auditfile),'connection_report_sha256':sha(dest/'connections.json')};summary.append(report);print(json.dumps({k:report[k] for k in ('design','connections','scalar_increased','rc_increased','max_scalar_ratio')}),flush=True)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':summary},indent=2)+'\n')
if __name__=='__main__':main()
