"""Explain simulated worsening using unchanged and replaced net ownership."""
import json,collections,shutil
from pathlib import Path
from array import array
from prepared_csr import read
from pre_route_endpoints import sha

def run():
 base=Path('experiments');parent=base/'conv_layer_length_switch_prediction_v2_2026-10-06';impact=base/'conv_layer_shared_tree_whole_net_candidate_impact_2026-10-06/report.json';search=base/'conv_layer_shared_tree_avoidance_2026-10-06'
 p=json.loads((parent/'protocol.json').read_text());pr=json.loads((parent/'receipt.json').read_text());r=json.loads(impact.read_text());sr=json.loads((search/'receipt.json').read_text());assert sha(parent/'prediction.json')==pr['prediction_sha256'] and sr['journal_sha256']==sha(search/'queries.jsonl')
 assert all(sha(path)==h for path,h in r['inputs_sha256'].items())
 m,f=read(base/'conv_layer_length_switch_csr_2026-10-06/csr',p['inputs']['graph']['sha256']);assert sha(base/'conv_layer_length_switch_csr_2026-10-06/csr/manifest.json')==p['csr_manifest_sha256']
 slots=array('Q',[0])*m['edges']
 for slot,eid in enumerate(f['edge_ids']):slots[eid]=slot
 selected={v['node'] for v in r['worsened_resources']};eligible=set(r['eligible_whole_net_ids']);old=collections.defaultdict(set);new=collections.defaultdict(set)
 def touched(source,path):
  current=source;seen={source}
  for eid in path:
   slot=slots[eid];assert f['row_offsets'][current]<=slot<f['row_offsets'][current+1];current=f['dest_ranks'][slot];assert current not in seen;seen.add(current)
  return seen&selected
 for row in json.loads((parent/'prediction.json').read_text())['connections']:
  for n in touched(row['source'],row['physical_edge_ids']):old[n].add(row['net_id'])
 for row in [json.loads(line) for line in (search/'queries.jsonl').read_text().splitlines()]:
  if row['net_id'] not in eligible:continue
  assert row['result']['status']=='FOUND'
  for n in touched(row['source'],row['result']['physical_edge_ids']):new[n].add(row['net_id'])
 records=[]
 for row in r['worsened_resources']:
  n=row['node'];unchanged=old[n]-eligible;after=unchanged|new[n];assert len(old[n])==row['old'] and len(after)==row['new'];assert max(0,len(after)-f['capacities'][n])==row['new_overflow']
  records.append({**row,'capacity':f['capacities'][n],'type':{v:k for k,v in m['type_codes'].items()}[f['types'][n]],'unchanged_owner_net_ids':sorted(unchanged),'old_replaced_owner_net_ids':sorted(old[n]&eligible),'new_replaced_owner_net_ids':sorted(new[n]),'introduced_owner_net_ids':sorted(new[n]-old[n])})
 report={'input_sha256':{str(impact):sha(impact),str(parent/'prediction.json'):sha(parent/'prediction.json'),str(search/'queries.jsonl'):sha(search/'queries.jsonl')},'worsened_resources':records,'resources_with_unchanged_owners':sum(bool(v['unchanged_owner_net_ids']) for v in records),'resources_without_unchanged_owners':sum(not v['unchanged_owner_net_ids'] for v in records),'resource_types':dict(collections.Counter(v['type'] for v in records)),'scope':'simulated predicted net ownership only; not actual native routing ownership or causal hotspot proof; no repair committed'}
 out=base/'conv_layer_shared_tree_conflict_ownership_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['input_sha256','worsened_resources']}),flush=True)
if __name__=='__main__':run()
