"""Replay additive physical channel span independently of search objective callback."""
import json,shutil
from pathlib import Path
from array import array
from prepared_csr import read
from pre_route_endpoints import sha

def run():
 base=Path('experiments');a=base/'conv_layer_strict_channel_avoidance_2026-10-06';b=base/'conv_layer_budgeted_span_avoidance_2026-10-06'
 data=[];inputs={}
 for root in [a,b]:
  p=json.loads((root/'protocol.json').read_text());r=json.loads((root/'receipt.json').read_text())
  assert r['protocol_sha256']==sha(root/'protocol.json') and r['journal_sha256']==sha(root/'queries.jsonl')
  for file in ['protocol.json','receipt.json','queries.jsonl']:inputs[str(root/file)]=sha(root/file)
  data.append((p,[json.loads(v) for v in (root/'queries.jsonl').read_text().splitlines()]))
 for key in ['inputs_sha256','graph','policy','banned_channel_nodes']:assert data[0][0][key]==data[1][0][key]
 m,f=read(base/'conv_layer_length_switch_csr_2026-10-06/csr',data[0][0]['graph']['sha256']);slots=array('Q',[0])*m['edges']
 for slot,eid in enumerate(f['edge_ids']):slots[eid]=slot
 def span(row):
  current=row['source'];total=0
  for eid in row['result']['physical_edge_ids']:
   slot=slots[eid];assert f['row_offsets'][current]<=slot<f['row_offsets'][current+1];current=f['dest_ranks'][slot]
   if f['types'][current] in (4,5):total+=max(f['xhigh'][current]-f['xlow'][current],f['yhigh'][current]-f['ylow'][current])+1
  assert current==row['sink'];return total
 rows=[]
 assert len(data[0][1])==len(data[1][1])==75
 for old,new in zip(data[0][1],data[1][1]):
  for key in ['connection_id','net_id','source','sink','original_opin','original_ipin']:assert old[key]==new[key]
  assert old['result']['status']==new['result']['status']
  if new['result']['status']!='FOUND':continue
  x,y=span(old),span(new);assert y==new['result']['cost'] and y<=x
  rows.append({'connection_id':new['connection_id'],'min_delay_span':x,'budgeted_span':y})
 assert len(rows)==65 and all(sha(p)==h for p,h in inputs.items())
 report={'inputs_sha256':inputs,'all_reported_costs_match_physical_span':True,'all_65_span_candidates_no_worse_than_min_delay':True,'improved_paths':sum(v['budgeted_span']<v['min_delay_span'] for v in rows),'total_min_delay_path_span':sum(v['min_delay_span'] for v in rows),'total_budgeted_path_span':sum(v['budgeted_span'] for v in rows),'rows':rows,'scope':'additive per-path objective replay only; does not prove net-union span, lower congestion, STA or accepted feedback'}
 out=base/'conv_layer_candidate_span_objective_replay_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['rows','inputs_sha256']}),flush=True)
if __name__=='__main__':run()
