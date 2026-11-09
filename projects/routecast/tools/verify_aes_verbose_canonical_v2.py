import json,re,sys
from pathlib import Path
from collections import Counter
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/aes_verbose_canonical_v1_2026-10-08';receipt=out/'receipt.json';data=json.loads(receipt.read_text());assert all(sha(k)==v for k,v in data['bindings'].items());bindings={str(receipt):sha(receipt),str(Path(__file__)):sha(Path(__file__))};rows=[]
pattern=re.compile(r"Fixed up net '([^']*)' mapping mismatch at clustered block '(.*)' pin 'grid\[(\d+)\]\[(\d+)\]\.([^.]*)\.([^\[]*)\[(\d+)\] - layer (\d+)' \(was net '([^']*)'\)")
for row in data['rows']:
 assert all(sha(k)==v for k,v in row['files'].items());name=row['name'];w=out/(row['trial']+'_'+name);log=(w/'reload.log').read_text();ids=R/f'experiments/aes_ignored_identity_v1_2026-10-08/{name}/identity.jsonl';ignored={x['name'] for x in map(json.loads,ids.read_text().splitlines()) if x['ignored']};endpoint=R/f'experiments/aes_rr_graph_only_v1_2026-10-08/{name}/endpoints.json';ep=json.loads(endpoint.read_text());names={ep['net_names'][str(q['net_id'])] for q in ep['connections']};ignored &= names;bindings[str(endpoint)]=sha(endpoint);table=R/'experiments'/row['trial']/(name+'_canonical')/'identity.jsonl';expected=Counter()
 for net in map(json.loads,table.read_text().splitlines()):
  if net['name'] in ignored:
   for pin in net['pins']:
    if pin['index']>0:expected[net['name'],pin['block'],pin['x'],pin['y'],pin['layer'],pin['port'],pin['bit']]+=1
 observed=Counter()
 for m in pattern.finditer(log):
  routed,block,x,y,tile,port,bit,layer,old=m.groups();assert routed=='unmapped' and old in ignored;observed[old,block,int(x),int(y),int(layer),port,int(bit)]+=1
 assert observed==expected,(name,len(observed),len(expected),list((observed-expected).items())[:2],list((expected-observed).items())[:2]);assert sum(observed.values())==row['mismatches']==row['fixups']
 assert (w/'design.net').read_bytes()==(w/'design.net.post_routing').read_bytes()
 for p in [ids,table,w/'design.net',w/'design.net.post_routing']:bindings[str(p)]=sha(p)
 rows.append({'trial':row['trial'],'name':name,'every_mismatch_matches_native_ignored_sink_pin':True,'mismatch_pin_occurrences':sum(observed.values()),'post_reload_packed_netlist_byte_identical':True,'strict_zero_counter_gate_pass':False,'scope':'All reported mismatch pins independently match pre-reload canonical identity; final packed netlist byte unchanged. Native counters remain nonzero, no waiver of old gate.'})
assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n');print(json.dumps(rows,indent=2))
