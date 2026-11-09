"""Verify isolated cost intervention and identical initial state/first-round schedule."""
import json,sys
from pathlib import Path
R=Path.cwd();sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
out=R/'experiments/aes_native_demand_uniform_channel_v1_2026-10-08';bindings={str(Path(__file__)):sha(Path(__file__))};rows=[]
a=R/'tools/run_resident_soft_demand_affected_cache_v1.py';b=R/'tools/run_resident_soft_demand_uniform_channel_v1.py';expected=a.read_text().replace("max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1",'1').replace('1/20 per destination CHAN span','1/20 per destination CHAN node (uniform, span removed)');assert b.read_text()==expected;bindings.update({str(a):sha(a),str(b):sha(b)})
for name in ['aes_cipher','aes_inv_cipher']:
 base=R/f'experiments/aes_native_demand_estimates_v1_2026-10-08/{name}/resident';control=out/name/'resident'
 for root in [base,control]:
  receipt=root/'receipt.json';d=json.loads(receipt.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());assert all(sha(k)==v for k,v in d['files'].items());bindings[str(receipt)]=sha(receipt)
 for file in ['initial.json','floors.json']:assert json.loads((base/file).read_text())==json.loads((control/file).read_text());bindings[str(base/file)]=sha(base/file);bindings[str(control/file)]=sha(control/file)
 x=json.loads((base/'receipt.json').read_text());y=json.loads((control/'receipt.json').read_text());assert x['rounds'][0]['affected_nets']==y['rounds'][0]['affected_nets'];assert x['rounds'][0]['changed_nodes']==y['rounds'][0]['changed_nodes'];p=json.loads((base/'protocol.json').read_text());q=json.loads((control/'protocol.json').read_text());assert p['rounds']==q['rounds']==2 and p['price_unit_integer']==q['price_unit_integer'] and p['required_connections']==q['required_connections'];assert y['rounds'][0]['overflow_before']==x['rounds'][0]['overflow_before']
 rows.append({'name':name,'only_static_span_cost_and_descriptive_protocol_changed':True,'initial_state_paths_floors_budgets_and_both_ledgers_exact':True,'first_round_affected_NET_schedule_and_initial_overuse_exact':True,'required_queries':q['required_connections'],'original_span_overflow':x['rounds'][-1]['overflow_after'],'removed_span_overflow':y['rounds'][-1]['overflow_after'],'scope':'Later schedules may causally diverge as changed occupancy differs; not heldout or native-quality gain.'})
assert all(sha(k)==v for k,v in bindings.items());(out/'control_verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n');print(rows)
