"""Necessary fixed-pin residual-capacity conditions for one-net replacement."""
import json,array,sys,collections,shutil
from pathlib import Path
from pre_route_endpoints import sha

def run():
 base=Path('experiments');parent=base/'conv_layer_length_switch_prediction_v2_2026-10-06';search=base/'conv_layer_budgeted_span_avoidance_2026-10-06';csr=base/'conv_layer_length_switch_csr_2026-10-06/csr'
 p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());sr=json.loads((search/'receipt.json').read_text());sp=json.loads((search/'protocol.json').read_text());m=json.loads((csr/'manifest.json').read_text())
 assert sha(csr/'manifest.json')==p['csr_manifest_sha256'] and sha(parent/'prediction.json')==r['prediction_sha256'] and sha(search/'queries.jsonl')==sr['journal_sha256'] and sha(search/'protocol.json')==sr['protocol_sha256']
 assert all(sha(path)==h for path,h in sp['inputs_sha256'].items())
 data={}
 for name in ['capacities','types']:
  spec=m['files'][name];path=csr/spec['file'];assert sha(path)==spec['sha256'];a=array.array(spec['type']);a.frombytes(path.read_bytes())
  if sys.byteorder!='little':a.byteswap()
  data[name]=a
 occupancy=json.loads((parent/'prediction.json').read_text())['node_occupancy'];rows=[json.loads(line) for line in (search/'queries.jsonl').read_text().splitlines()];nets=collections.defaultdict(list)
 for row in rows:
  pins=[]
  for key,kind in [('source',0),('original_opin',2),('original_ipin',3),('sink',1)]:
   n=row[key];assert data['types'][n]==kind;old=occupancy[str(n)];assert old>=1;other=old-1;cap=data['capacities'][n]
   pins.append({'role':key,'node':n,'capacity':cap,'other_predicted_net_owners':other,'room_after_removing_this_net':other<cap})
  nets[row['net_id']].append({'connection_id':row['connection_id'],'pins':pins,'necessary_pin_condition_pass':all(v['room_after_removing_this_net'] for v in pins)})
 report={'inputs_sha256':{str(parent/'prediction.json'):sha(parent/'prediction.json'),str(search/'queries.jsonl'):sha(search/'queries.jsonl'),str(csr/'manifest.json'):sha(csr/'manifest.json')},'whole_nets':{str(n):{'all_fixed_pin_conditions_pass':all(v['necessary_pin_condition_pass'] for v in values),'connections':values} for n,values in sorted(nets.items())},'scope':'necessary fixed original pin conditions for isolated one-net zero-overuse replacement, all other predicted net ownership fixed; not sufficient route feasibility or batch impossibility, native ownership or STA'}
 out=base/'conv_layer_fixed_pin_residual_screen_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'nets':len(nets),'pin_condition_blocked_nets':sum(not v['all_fixed_pin_conditions_pass'] for v in report['whole_nets'].values()),'pin_condition_pass_nets':sum(v['all_fixed_pin_conditions_pass'] for v in report['whole_nets'].values())}))
if __name__=='__main__':run()
