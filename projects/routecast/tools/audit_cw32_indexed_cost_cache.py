"""Full frozen-cohort exact lattice parity with independent Fraction search."""
import json,time,shutil
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from prepared_csr import read,U64
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from csr_integer_budget_search import query
from pre_route_endpoints import sha
from cost_read_dependency_index import CostReadDependencyIndex

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_indexed_cost_cache_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('audit_cw32_indexed_cost_cache.py','cost_read_dependency_index.py','integer_rc_context.py','csr_integer_budget_search.py','csr_exact_buffered_rc.py','prepared_csr.py','buffered_rc_context.py','buffered_rc_node_classes.py','pre_route_endpoints.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 protocol={'cohort':[f'mult_{w}x{w}' for w in range(4,10)],'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'scope':'Exact LCM-scaled delay, all first-pass queries and wholeNET admission same as archived Fraction driver. No integer-width cap/hardware claim. Warm all queries at initial state then replay actual wholeNET admissions; invalidate otherNET cost-read dependencies after each commit. Every query checked with fresh full oracle and archived Fraction result. Warm and oracle costs charged separately, no performance gain claim; no placement move or concurrent publication.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');reports=[]
 for name in protocol['cohort']:
  start=time.monotonic();dest=out/name;dest.mkdir();parent=root/'experiments/multiplier_cw32_rc_budgeted_nets_2026-10-06'/name;prior=json.loads((parent/'receipt.json').read_text());assert sha(parent/'queries.jsonl')==prior['queries_sha256'];truth={r['connection_id']:r['result'] for r in map(json.loads,(parent/'queries.jsonl').read_text().splitlines())};baseline=root/'experiments/multiplier_family_predictions_cw32_2026-10-06'/name/'sparse_reset';pred=json.loads((baseline/'prediction.json').read_text());context=root/'experiments/multiplier_cw32_exact_buffered_rc_classes_2026-10-06'/name;budgets={r['connection_id']:Fraction(*r['exact_delay_s']) for r in json.loads((context/'baseline_budgets.json').read_text())};m,f=read(root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name/'csr',pred['physical_graph_sha256']);rc=ExactBufferedRC(f,*load(context,pred['physical_graph_sha256']));t=time.monotonic();integer=IntegerRC(rc);init_s=time.monotonic()-t;groups=defaultdict(list);edge={f['edge_ids'][i]:(n,f['dest_ranks'][i]) for n in range(m['nodes']) for i in range(f['row_offsets'][n],f['row_offsets'][n+1])}
  for r in pred['connections']:groups[r['net_id']].append(r)
  def union(rows):
   nodes=set()
   for r in rows:
    nodes.add(r['source'])
    for e in r['physical_edge_ids']:nodes.update(edge[e])
   return nodes
  unions={n:union(rows) for n,rows in groups.items()};occ=Counter(n for nodes in unions.values() for n in nodes);overflow=lambda values:sum(max(0,v-f['capacities'][n]) for n,v in values.items());checked=0;t=time.monotonic()
  cache={};index=CostReadDependencyIndex((pred['physical_graph_sha256'],sha(context/'baseline_budgets.json')));hits=misses=invalidations=0;events=[]
  allowed=lambda u,i:f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0
  def search(r,other):
   footprint=set()
   def cost(u,i):
    n=f['dest_ranks'][i];footprint.add(n);return int(f['costs'][i])*(1+other[n])
   result=query(integer,r['source'],r['sink'],integer.encode(budgets[r['connection_id']]),allowed,cost,10000)
   return result,footprint
  # Warm every query at the actual initial occupancy, excluding its own NET.
  warm_start=time.monotonic()
  for net,rows in sorted(groups.items()):
   other=occ.copy();other.subtract(unions[net])
   for r in rows:
    result,footprint=search(r,other)
    if result['status']=='FOUND':cache[r['connection_id']]=(net,result,footprint);index.register(r['connection_id'],net,footprint)
  warm_s=time.monotonic()-warm_start;sequence_start=time.monotonic()
  for net,rows in sorted(groups.items()):
   other=occ.copy();other.subtract(unions[net]);candidate=[]
   for r in rows:
    cid=r['connection_id'];entry=cache.get(cid)
    if entry is None:
     result,footprint=search(r,other);misses+=1
     if result['status']=='FOUND':cache[cid]=(net,result,footprint);index.register(cid,net,footprint)
    else:result=entry[1];hits+=1
    full,_=search(r,other)
    assert all(result[k]==full[k] for k in ('status','physical_edge_ids','cost','delay'))
    old=truth[cid];assert result['status']==old['status'] and result['physical_edge_ids']==old['physical_edge_ids'] and result['cost']==old['cost']
    assert Fraction(result['delay'],integer.scale)==Fraction(old['delay'])
    candidate.append({**r,'physical_edge_ids':result['physical_edge_ids']});checked+=1
   staged=other.copy();newunion=union(candidate);staged.update(newunion)
   accepted=overflow(staged)<=overflow(occ);dirty=set();removed=0
   if accepted:
    dirty=unions[net]^newunion;occ=staged;unions[net]=newunion
    # The changed NET's own contribution cancels in its query costs.
    doomed=[cid for cid,(owner,result,footprint) in cache.items() if owner!=net and dirty&footprint]
    indexed=index.invalidate(dirty,excluded_owner=net);assert indexed==set(doomed)
    for cid in indexed:del cache[cid]
    assert set(index.entries)==set(cache)
    removed=len(doomed);invalidations+=removed
   events.append({'net_id':net,'accepted':accepted,'dirty_occupancy_nodes':len(dirty),'invalidated_queries':removed,'overflow':overflow(occ)})
  (dest/'events.json').write_text(json.dumps(events,indent=2)+'\n')
  sequence_s=time.monotonic()-sequence_start
  report={'design':name,'queries_exact_same_path_cost_delay':checked,'final_overflow':overflow(occ),'scale_bits':integer.scale.bit_length(),'cache_hits':hits,'cache_misses':misses,'invalidations':invalidations,'warm_search_s':warm_s,'sequence_with_full_oracle_s':sequence_s,'events_sha256':sha(dest/'events.json'),'context_conversion_s':init_s,'search_and_state_s':time.monotonic()-t,'driver_wall_s':time.monotonic()-start};assert report['final_overflow']==prior['final_overflow'];reports.append(report);print(json.dumps(report),flush=True)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':reports},indent=2)+'\n')
if __name__=='__main__':main()
